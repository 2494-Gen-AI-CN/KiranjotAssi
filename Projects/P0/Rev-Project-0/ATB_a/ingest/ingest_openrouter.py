"""Validate and batch-load OpenRouter prices."""

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
import pandas as pd
import yaml
from dotenv import load_dotenv
from google.cloud import bigquery


PRICE_FIELDS = {
    "model_id": "STRING",
    "snapshot_date": "DATE",
    "prompt_usd_per_m": "NUMERIC",
    "completion_usd_per_m": "NUMERIC",
    "context_length": "INT64",
    "is_free_variant": "BOOL",
    "is_batch_variant": "BOOL",
}
AUDIT_FIELDS = {"source_file": "STRING", "run_id": "STRING"}
REJECT_FIELDS = {
    **AUDIT_FIELDS, "line_number": "INT64", "record_id": "STRING", "reason": "STRING"
}
SUPPORT_LOG_FIELDS = {
    "run_id": "STRING", "staging_table": "STRING", "started_at": "TIMESTAMP",
    "finished_at": "TIMESTAMP", "rows_read": "INT64", "rows_loaded": "INT64",
    "rows_rejected": "INT64", "rows_filtered": "INT64", "status": "STRING",
}
PRICE_COLUMNS = ("prompt_usd_per_m", "completion_usd_per_m")


@dataclass
class Counts:
    rows_read: int = 0
    rows_accepted: int = 0
    rows_rejected: int = 0
    rows_filtered: int = 0


def write_jsonl(output, row):
    output.write(json.dumps(row, ensure_ascii=False) + "\n")


def now():
    return datetime.now(timezone.utc).isoformat()


def load_file(client, path, table, fields, disposition):
    from google.cloud import bigquery

    if path.stat().st_size == 0:
        columns = ", ".join(f"`{name}` {kind}" for name, kind in fields.items())
        client.query(f"CREATE OR REPLACE TABLE `{table}` ({columns})").result()
        return 0

    config = bigquery.LoadJobConfig(
        schema=[bigquery.SchemaField(name, kind) for name, kind in fields.items()],
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=disposition,
    )
    with path.open("rb") as source:
        job = client.load_table_from_file(
            source, table, size=path.stat().st_size, job_config=config
        )
        job.result()
    return job.output_rows


def required_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonblank text")
    return value.strip()


def number(value, field):
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"{field} must be numeric") from None
    if not result.is_finite():
        raise ValueError(f"{field} must be finite")
    return result


def whole_number(value, field, minimum):
    result = number(value, field)
    if result != result.to_integral_value() or not minimum <= result < 2**63:
        raise ValueError(f"{field} must be a whole number from {minimum} to {2**63 - 1}")
    return int(result)


def price(value, field):
    if value in (None, ""):
        return None
    result = number(value, field)
    # The observed catalog sentinel is -1 USD/token, or -1 million USD/million tokens.
    if result == -1_000_000:
        return None
    if result < 0:
        raise ValueError(f"{field} has an unexpected negative price")
    if result >= Decimal("1e29"):
        raise ValueError(f"{field} is outside BigQuery NUMERIC precision")
    # The CSV's per-million values were calculated with binary floating point.
    with localcontext() as context:
        context.prec = 40
        if result.as_tuple().exponent < -9:
            result = round(result, 9)
    if result >= Decimal("1e29"):
        raise ValueError(f"{field} is outside BigQuery NUMERIC precision")
    return format(result, "f")


def boolean(value, field):
    if isinstance(value, str):
        value = value.strip().lower()
        if value in {"true", "false"}:
            return value == "true"
    if type(value) is bool:
        return value
    raise ValueError(f"{field} must be true or false")


def clean_price(row, date):
    return {
        "model_id": required_text(row.get("model_id"), "model_id"),
        "snapshot_date": date,
        **{field: price(row.get(field), field) for field in PRICE_COLUMNS},
        "context_length": whole_number(row["context_length"], "context_length", 1)
        if row.get("context_length") not in (None, "") else None,
        "is_free_variant": boolean(row.get("is_free_variant"), "is_free_variant"),
        "is_batch_variant": boolean(row.get("is_batch_variant"), "is_batch_variant"),
    }


def input_records(path):
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        header = reader.fieldnames or []
        required = set(PRICE_FIELDS) - {"context_length"}
        if len(header) != len(set(header)) or required - set(header):
            raise ValueError(f"{path.name}: invalid CSV header or missing price columns")
        for row in reader:
            error = "CSV row does not match header" if None in row or None in row.values() else None
            yield reader.line_num, row, error


def prepare_group(root, sources, good_path, bad_path, run_id, counts):
    date_field = "snapshot_date"
    id_field = "model_id"
    seen = set()

    with good_path.open("w", encoding="utf-8") as good, bad_path.open("w", encoding="utf-8") as bad:
        for source in sources:
            path = root / source["path"]
            audit = {"source_file": path.name, "run_id": run_id}
            batch = []

            def reject(line, row, reason):
                identifier = row.get(id_field)
                write_jsonl(bad, {
                    **audit, "line_number": line, "reason": reason,
                    "record_id": identifier if isinstance(identifier, str) else None,
                })
                counts.rows_rejected += 1

            def process_batch():
                dates = pd.Series([row.get(date_field) for _, row in batch], dtype="string")
                dates = dates.where(dates.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False))
                parsed = pd.to_datetime(dates, format="%Y-%m-%d", errors="coerce")
                for (line, row), date in zip(batch, parsed):
                    try:
                        if pd.isna(date):
                            raise ValueError(f"{date_field} must be a valid YYYY-MM-DD date")
                        date_text = date.date().isoformat()
                        cleaned = clean_price(row, date_text)
                        key = (cleaned["model_id"], date_text)
                        if key in seen:
                            raise ValueError("duplicate source key")
                    except ValueError as error:
                        reject(line, row, str(error))
                    else:
                        seen.add(key)
                        write_jsonl(good, {**cleaned, **audit})
                        counts.rows_accepted += 1
                batch.clear()

            for line, row, error in input_records(path):
                counts.rows_read += 1
                if error:
                    reject(line, row, error)
                else:
                    batch.append((line, row))
                    if len(batch) == 5000:
                        process_batch()
            if batch:
                process_batch()


def run_group(root, settings, sources, client):
    table = "stg_openrouter"
    run_id = uuid4().hex
    started_at = now()
    counts = Counts()
    loaded = 0
    status = "failed"
    project = settings["project_id"]
    stage = f"{project}.{settings['staging_dataset']}"
    ops = f"{project}.{settings['operations_dataset']}"
    with TemporaryDirectory() as temporary:
        good, bad, log = (Path(temporary) / name for name in ("accepted.jsonl", "rejects.jsonl", "log.jsonl"))
        try:
            prepare_group(root, sources, good, bad, run_id, counts)
            print(
                f"{table}: read {counts.rows_read:,} | accepted {counts.rows_accepted:,} "
                f"| rejected {counts.rows_rejected:,} | filtered {counts.rows_filtered:,}"
            )
            if client is None:
                with bad.open(encoding="utf-8") as rejects:
                    for index, row in enumerate(rejects):
                        if index == 5:
                            break
                        print(row.rstrip())
                return
            if not counts.rows_accepted:
                raise ValueError(f"No accepted rows for {table}; the staging table was preserved")
            loaded = load_file(client, good, f"{stage}.{table}", {**PRICE_FIELDS, **AUDIT_FIELDS}, "WRITE_TRUNCATE")
            load_file(client, bad, f"{ops}.openrouter_rejects", REJECT_FIELDS, "WRITE_TRUNCATE")
            status = "success"
        finally:
            if client is not None:
                log_counts = asdict(counts)
                del log_counts["rows_accepted"]
                with log.open("w", encoding="utf-8") as output:
                    write_jsonl(output, {
                        **log_counts, "rows_loaded": loaded, "staging_table": table,
                        "run_id": run_id, "started_at": started_at,
                        "finished_at": now(), "status": status,
                    })
                try:
                    load_file(client, log, f"{ops}.openrouter_load_log", SUPPORT_LOG_FIELDS, "WRITE_APPEND")
                except Exception as error:
                    if status == "success":
                        raise
                    print(f"Could not write failed run to the load log: {error}")


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8-sig"))
    settings = config["bigquery"]
    table = "stg_openrouter"
    sources = [entry for entry in config["sources"] if entry.get("staging_table") == table]
    file_format = "csv"
    if not sources or any(entry.get("format") != file_format for entry in sources):
        parser.error(f"Configure {file_format} sources for {table} in config.yaml")

    client = None
    if not args.dry_run:
        load_dotenv(root / ".env")
        client = bigquery.Client(project=settings["project_id"], location=settings["location"])
    run_group(root, settings, sources, client)


if __name__ == "__main__":
    main()
