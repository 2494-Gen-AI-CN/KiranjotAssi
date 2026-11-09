"""Data validation and batch-load the data into BigQuery"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import dataclass
from uuid import uuid4
import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery
import yaml

TEXT_FIELDS = ("id", "model_a", "model_b", "winner")

WINNERS = {"model_a", "model_b", "tie", "both_bad"}

COUNTS = ("header_count", "list_count", "bold_count")

BATTLE_SCHEMA = {
    "id": "STRING", 
    "timestamp": "TIMESTAMP", 
    "model_a": "STRING",
    "model_b": "STRING", 
    "winner": "STRING", 
    "language": "STRING",
    "is_code": "BOOL", 
    "category_tag_json": "STRING",
    "answer_tokens_a": "INT64", 
    "answer_tokens_b": "INT64",
    **{f"{count}_{side}": "INT64" for side in ("a", "b") for count in COUNTS},
    "source_shard": "STRING", 
    "run_id": "STRING",
}
REJECT_SCHEMA = {
    "source_file": "STRING", 
    "line_number": "INT64", 
    "battle_id": "STRING",
    "reason": "STRING", 
    "source_shard": "STRING",
}
LOG_SCHEMA = {
    "run_id": "STRING", 
    "started_at": "TIMESTAMP", 
    "finished_at": "TIMESTAMP",
    "rows_read": "INT64", 
    "rows_loaded": "INT64", 
    "rows_rejected": "INT64",
    "status": "STRING",
}


@dataclass
class Counts:
    rows_read: int = 0
    rows_accepted: int = 0
    rows_rejected: int = 0


def optional_count(value):
    if value is not None and (type(value) is not int or value < 0):
        raise ValueError("metadata count must be a non-negative integer")
    return value


def formatting_total(value):
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("formatting counts must be an object")
    counts = [optional_count(count) for count in value.values()]
    return sum(counts) if counts and None not in counts else None


def clean_batch(records, seen_ids, run_id):
    # Keep the original JSON types while pandas normalizes the text and dates.
    frame = pd.DataFrame(records, columns=[*TEXT_FIELDS, "timestamp"], dtype=object)
    for field in TEXT_FIELDS:
        frame[field] = frame[field].map(
            lambda value: value.strip() if isinstance(value, str) else ""
        )
    frame["winner"] = frame["winner"].str.lower()
    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"].map(lambda value: value if isinstance(value, str) else None),
        format="ISO8601", errors="coerce", utc=True,
    )

    for original, normalized in zip(records, frame.to_dict("records")):
        try:
            if not all(normalized[field] for field in TEXT_FIELDS):
                raise ValueError("missing or invalid id, model name, or winner")
            if pd.isna(normalized["timestamp"]):
                raise ValueError("missing or invalid timestamp")
            if normalized["winner"] not in WINNERS:
                raise ValueError("unrecognized winner")
            if normalized["model_a"] == normalized["model_b"]:
                raise ValueError("self-match")
            if normalized["id"] in seen_ids:
                raise ValueError("duplicate vote id")

            metadata = original.get("conv_metadata")
            if metadata is None:
                metadata = {}
            if not isinstance(metadata, dict):
                raise ValueError("conv_metadata must be an object")
            language = original.get("language")
            if language is not None and not isinstance(language, str):
                raise ValueError("language must be text")
            is_code = original.get("is_code")
            if is_code is not None and type(is_code) is not bool:
                raise ValueError("is_code must be boolean")
            tags = original.get("category_tag")
            if tags is not None and not isinstance(tags, dict):
                raise ValueError("category_tag must be an object")

            normalized["timestamp"] = normalized["timestamp"].isoformat(timespec="microseconds")
            normalized.update(
                language=(language.strip() or None) if language else None,
                is_code=is_code,
                category_tag_json=json.dumps(tags) if tags is not None else None,
                source_shard=original.get("source_shard"),
                run_id=run_id,
            )
            for side in ("a", "b"):
                normalized[f"answer_tokens_{side}"] = optional_count(
                    metadata.get(f"sum_assistant_{side}_tokens")
                )
                for count in COUNTS:
                    field = f"{count}_{side}"
                    normalized[field] = formatting_total(metadata.get(field))
        except ValueError as error:
            yield None, str(error)
        else:
            seen_ids.add(normalized["id"])
            yield normalized, None


def write_jsonl(output, row):
    output.write(json.dumps(row, ensure_ascii=False) + "\n")


def prepare_files(paths, accepted_path, rejected_path, run_id, counts):
    seen_ids = set()
    with accepted_path.open("w", encoding="utf-8") as good, rejected_path.open(
        "w", encoding="utf-8"
    ) as bad:
        for path in paths:
            def process_batch(batch):
                records = [record for _, record in batch]
                for (line, raw), (row, reason) in zip(
                    batch, clean_batch(records, seen_ids, run_id)
                ):
                    if reason is None:
                        write_jsonl(good, row)
                        counts.rows_accepted += 1
                    else:
                        reject(line, raw, reason)

            def reject(line, raw, reason):
                write_jsonl(bad, {
                    "source_file": path.name, "line_number": line,
                    "battle_id": raw.get("id") if isinstance(raw.get("id"), str) else None,
                    "source_shard": raw.get("source_shard"),
                    "reason": reason,
                })
                counts.rows_rejected += 1

            with path.open(encoding="utf-8-sig") as source:
                batch = []
                for line_number, line in enumerate(source, start=1):
                    counts.rows_read += 1
                    try:
                        record = json.loads(line)
                        if not isinstance(record, dict):
                            raise ValueError("record must be a JSON object")
                    except ValueError as error:
                        reject(line_number, {}, str(error))
                        continue
                    batch.append((line_number, record))
                    if len(batch) == 5000:
                        process_batch(batch)
                        batch.clear()
                if batch:
                    process_batch(batch)


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


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    config = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8-sig"))
    settings = config["bigquery"]
    sources = [source for source in config["sources"] if source.get("staging_table") == "stg_battles"]
    if not sources or any(source["format"] != "json" for source in sources):
        parser.error("Configure at least one JSONL source for stg_battles in config.yaml")

    run_id = uuid4().hex
    started_at = now()
    project = settings["project_id"]
    stage = f"{project}.{settings['staging_dataset']}"
    ops = f"{project}.{settings['operations_dataset']}"
    with TemporaryDirectory() as temporary:
        work = Path(temporary)
        good, bad, log = (work / name for name in ("accepted.jsonl", "rejects.jsonl", "log.jsonl"))
        client = None
        if not args.dry_run:
            load_dotenv(root / ".env")
            client = bigquery.Client(project=project, location=settings["location"])

        counts = Counts()
        loaded = 0
        status = "failed"
        try:
            prepare_files(
                [root / source["path"] for source in sources], good, bad, run_id, counts
            )
            print(
                f"Read {counts.rows_read:,} | Accepted {counts.rows_accepted:,} "
                f"| Rejected {counts.rows_rejected:,}"
            )
            if args.dry_run:
                return
            if not counts.rows_accepted:
                raise ValueError("No accepted battles. Check the export and dry-run counts.")
            loaded = load_file(client, good, f"{stage}.stg_battles", BATTLE_SCHEMA, "WRITE_TRUNCATE")
            load_file(client, bad, f"{ops}.arena_rejects", REJECT_SCHEMA, "WRITE_TRUNCATE")
            status = "success"
            print(f"Loaded {loaded:,} rows into {stage}.stg_battles")
        finally:
            if client is not None:
                with log.open("w", encoding="utf-8") as output:
                    write_jsonl(output, {
                        "run_id": run_id, "started_at": started_at, "finished_at": now(),
                        "rows_read": counts.rows_read, "rows_loaded": loaded,
                        "rows_rejected": counts.rows_rejected, "status": status,
                    })
                try:
                    load_file(client, log, f"{ops}.arena_load_log", LOG_SCHEMA, "WRITE_APPEND")
                except Exception as error:
                    if status == "success":
                        raise
                    print(f"Could not write the failed run to the load log: {error}")


if __name__ == "__main__":
    main()
