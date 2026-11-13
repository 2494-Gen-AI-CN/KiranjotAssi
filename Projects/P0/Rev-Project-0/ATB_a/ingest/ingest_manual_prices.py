"""Clean manual price evidence and load it separately from OpenRouter."""

import argparse
import json
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
from uuid import uuid4
from dotenv import load_dotenv
from google.cloud import bigquery
import pandas as pd
import yaml

from ingest_openrouter import load_file, now, number, write_jsonl


PRICE_FIELDS = {
    "arena_name": "STRING", "prompt_usd_per_m": "NUMERIC",
    "completion_usd_per_m": "NUMERIC", "blended_price_per_m": "NUMERIC",
    "provider": "STRING", "pricing_terms": "STRING", "price_status": "STRING",
    "source_url": "STRING", "checked_on": "DATE",
    "source_file": "STRING", "run_id": "STRING",
}
REJECT_FIELDS = {
    "source_file": "STRING", "line_number": "INT64",
    "reason": "STRING", "run_id": "STRING",
}
LOG_FIELDS = {
    "run_id": "STRING", "started_at": "TIMESTAMP", "finished_at": "TIMESTAMP",
    "rows_read": "INT64", "rows_loaded": "INT64", "rows_rejected": "INT64",
    "status": "STRING",
}


def clean_row(row):
    if not isinstance(row["arena_name"], str) or not row["arena_name"]:
        raise ValueError("arena_name is required")
    input_rate = number(row["prompt_usd_per_m"], "prompt_usd_per_m")
    output_rate = number(row["completion_usd_per_m"], "completion_usd_per_m")
    if not all(0 <= rate < Decimal("1e29") and rate.as_tuple().exponent >= -9
               for rate in (input_rate, output_rate)):
        raise ValueError("rates must be nonnegative BigQuery NUMERIC values")

    checked_on = row["checked_on"]
    if checked_on is not None and (
        not isinstance(checked_on, str) or date.fromisoformat(checked_on).isoformat() != checked_on
    ):
        raise ValueError("checked_on must use YYYY-MM-DD")
    url = row["source_url"]
    if url is not None and (
        not isinstance(url, str) or urlsplit(url).scheme not in ("http", "https")
        or not urlsplit(url).netloc
    ):
        raise ValueError("source_url must be an HTTP or HTTPS URL")
    if any(value is not None and not isinstance(value, str)
           for value in (row["provider"], row["pricing_terms"])):
        raise ValueError("provider and pricing_terms must be text")

    status = row["price_status"]
    if status not in ("provider_rate", "historical", "source_details_missing"):
        raise ValueError("price_status is invalid")
    if not all((row["provider"], row["pricing_terms"], url)):
        status = "source_details_missing"
    with localcontext() as context:
        context.prec = 40
        blended = round((input_rate + output_rate) / 2, 9)
    return {
        **row,
        "prompt_usd_per_m": format(input_rate, "f"),
        "completion_usd_per_m": format(output_rate, "f"),
        "blended_price_per_m": format(blended, "f"),
        "price_status": status,
    }


def prepare_files(root, sources, accepted, rejects, run_id):
    read = loaded = rejected = 0
    seen = set()
    raw_fields = PRICE_FIELDS.keys() - {"blended_price_per_m", "source_file", "run_id"}
    with accepted.open("w", encoding="utf-8") as good, rejects.open("w", encoding="utf-8") as bad:
        for source in sources:
            path = root / source["path"]
            records = []
            with path.open(encoding="utf-8-sig") as input_file:
                for line_number, line in enumerate(input_file, 1):
                    read += 1
                    try:
                        record = json.loads(line)
                        if not isinstance(record, dict):
                            raise ValueError("Expected a JSON object")
                    except ValueError as error:
                        write_jsonl(bad, {
                            "source_file": path.name, "line_number": line_number,
                            "reason": str(error), "run_id": run_id,
                        })
                        rejected += 1
                    else:
                        records.append({"line_number": line_number, **{
                            field: record.get(field) for field in raw_fields
                        }})

            frame = pd.DataFrame(records, dtype=object)
            for field in raw_fields & set(frame.columns):
                frame[field] = frame[field].map(
                    lambda value: (value.strip() or None) if isinstance(value, str) else value
                )
            frame = frame.astype(object).where(frame.notna(), None)
            for row in frame.to_dict("records"):
                line_number = row.pop("line_number")
                try:
                    cleaned = clean_row(row)
                    if cleaned["arena_name"] in seen:
                        raise ValueError("duplicate Arena model ID")
                except (TypeError, ValueError) as error:
                    write_jsonl(bad, {
                        "source_file": path.name, "line_number": line_number,
                        "reason": str(error), "run_id": run_id,
                    })
                    rejected += 1
                else:
                    seen.add(cleaned["arena_name"])
                    write_jsonl(good, {**cleaned, "source_file": path.name, "run_id": run_id})
                    loaded += 1
    return read, loaded, rejected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8-sig"))
    settings = config["bigquery"]
    sources = [s for s in config["sources"] if s.get("staging_table") == "stg_manual_prices"]
    if not sources or any(s.get("format") != "json" for s in sources):
        parser.error("Configure at least one JSONL source for stg_manual_prices")

    project = settings["project_id"]
    staging = f"{project}.{settings['staging_dataset']}"
    ops = f"{project}.{settings['operations_dataset']}"
    run_id, started = uuid4().hex, now()
    with TemporaryDirectory() as temporary:
        work = Path(temporary)
        good, bad, log = (work / name for name in ("accepted.jsonl", "rejects.jsonl", "log.jsonl"))
        read, accepted, rejected = prepare_files(root, sources, good, bad, run_id)
        print(f"Read {read:,} | Accepted {accepted:,} | Rejected {rejected:,}")
        if args.dry_run:
            return
        if not accepted:
            raise ValueError("No accepted manual prices. Run validation first.")

        load_dotenv(root / ".env")
        client = bigquery.Client(project=project, location=settings["location"])
        loaded, status = 0, "failed"
        try:
            loaded = load_file(client, good, f"{staging}.stg_manual_prices", PRICE_FIELDS, "WRITE_TRUNCATE")
            load_file(client, bad, f"{ops}.manual_prices_rejects", REJECT_FIELDS, "WRITE_TRUNCATE")
            status = "success"
        finally:
            with log.open("w", encoding="utf-8") as output:
                write_jsonl(output, {
                    "run_id": run_id, "started_at": started, "finished_at": now(),
                    "rows_read": read, "rows_loaded": loaded, "rows_rejected": rejected,
                    "status": status,
                })
            try:
                load_file(client, log, f"{ops}.manual_prices_load_log", LOG_FIELDS, "WRITE_APPEND")
            except Exception as error:
                if status == "success":
                    raise
                print(f"Could not write failed run to the load log: {error}")


if __name__ == "__main__":
    main()
