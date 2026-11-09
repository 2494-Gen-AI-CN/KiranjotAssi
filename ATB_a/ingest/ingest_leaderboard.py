"""Validate and batch-load both Arena leaderboard variants."""

import argparse
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery
import yaml


LEADERBOARD_FIELDS = {
    "model_name": "STRING",
    "leaderboard_publish_date": "DATE",
    "category": "STRING",
    "leaderboard_variant": "STRING",
    "rank": "INT64",
    "rating": "FLOAT64",
    "rating_lower": "FLOAT64",
    "rating_upper": "FLOAT64",
    "vote_count": "INT64",
    "organization": "STRING",
    "license": "STRING",
}
AUDIT_FIELDS = {
    "source_file": "STRING", 
    "run_id": "STRING"}

REJECT_FIELDS = {
    **AUDIT_FIELDS, 
    "line_number": "INT64", 
    "record_id": "STRING", 
    "reason": "STRING"
}

SUPPORT_LOG_FIELDS = {
    "run_id": "STRING", 
    "staging_table": "STRING", 
    "started_at": "TIMESTAMP",
    "finished_at": "TIMESTAMP", 
    "rows_read": "INT64", 
    "rows_loaded": "INT64",
    "rows_rejected": "INT64", 
    "rows_filtered": "INT64", 
    "status": "STRING",
}

VARIANTS = {
    "text", 
    "text_style_control"}


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


def optional_text(value, field):
    return None if value in (None, "") else required_text(value, field)


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


def rating(value, field):
    result = float(number(value, field))
    if not math.isfinite(result):
        raise ValueError(f"{field} is outside the FLOAT64 range")
    return result


def clean_leaderboard(row, date, variant):
    return {
        "model_name": required_text(row.get("model_name"), "model_name"),
        "leaderboard_publish_date": date,
        "category": required_text(row.get("category"), "category"),
        "leaderboard_variant": variant,
        "rank": whole_number(row.get("rank"), "rank", 1),
        "rating": rating(row.get("rating"), "rating"),
        **{
            field: rating(row[field], field) if row.get(field) is not None else None
            for field in ("rating_lower", "rating_upper")
        },
        "vote_count": whole_number(row["vote_count"], "vote_count", 0)
        if row.get("vote_count") is not None else None,
        "organization": optional_text(row.get("organization"), "organization"),
        "license": optional_text(row.get("license"), "license"),
    }


def input_records(path):
    with path.open(encoding="utf-8-sig", newline="") as source:
        for line_number, line in enumerate(source, 1):
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("expected a JSON object")
            except ValueError as error:
                yield line_number, {}, str(error)
            else:
                yield line_number, row, None


def prepare_group(root, sources, good_path, bad_path, run_id, counts):
    date_field = "leaderboard_publish_date"
    id_field = "model_name"
    seen = set()

    with good_path.open("w", encoding="utf-8") as good, bad_path.open("w", encoding="utf-8") as bad:
        for source in sources:
            path = root / source["path"]
            variant = source.get("leaderboard_variant")
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
                        cleaned = clean_leaderboard(row, date_text, variant)
                        key = (variant, cleaned["category"], date_text, cleaned["model_name"])
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
                elif row.get("leaderboard_variant") != variant:
                    reject(line, row, f"expected leaderboard_variant={variant}")
                elif not (isinstance(row.get("category"), str) and row["category"].strip()):
                    reject(line, row, "category must be nonblank text")
                elif row["category"].strip() != "overall":
                    counts.rows_filtered += 1
                else:
                    batch.append((line, row))
                    if len(batch) == 5000:
                        process_batch()
            if batch:
                process_batch()


def run_group(root, settings, sources, client):
    table = "stg_leaderboard"
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
            with good.open(encoding="utf-8") as output:
                variants = {json.loads(line)["leaderboard_variant"] for line in output}
            if variants != VARIANTS:
                raise ValueError("Both leaderboard variants need accepted rows before replacing staging")
            loaded = load_file(client, good, f"{stage}.{table}", {**LEADERBOARD_FIELDS, **AUDIT_FIELDS}, "WRITE_TRUNCATE")
            load_file(client, bad, f"{ops}.leaderboard_rejects", REJECT_FIELDS, "WRITE_TRUNCATE")
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
                    load_file(client, log, f"{ops}.leaderboard_load_log", SUPPORT_LOG_FIELDS, "WRITE_APPEND")
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
    table = "stg_leaderboard"
    sources = [entry for entry in config["sources"] if entry.get("staging_table") == table]
    file_format = "json"
    if not sources or any(entry.get("format") != file_format for entry in sources):
        parser.error(f"Configure {file_format} sources for {table} in config.yaml")
    if {entry.get("leaderboard_variant") for entry in sources} != VARIANTS:
        parser.error("Configure both text and text_style_control sources")

    client = None
    if not args.dry_run:
        load_dotenv(root / ".env")
        client = bigquery.Client(project=settings["project_id"], location=settings["location"])
    run_group(root, settings, sources, client)


if __name__ == "__main__":
    main()
