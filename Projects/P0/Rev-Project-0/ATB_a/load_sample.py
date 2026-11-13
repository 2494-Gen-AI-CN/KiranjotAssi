from pathlib import Path

import yaml
from google.cloud import bigquery

project_folder = Path(__file__).resolve().parent
config = yaml.safe_load(
    (project_folder / "config.yaml").read_text(encoding="utf-8")
)

settings = config["bigquery"]
source = config["sources"][0]
client = bigquery.Client(
    project=settings["project_id"],
    location=settings["location"],
)

destination = ".".join(
    [settings["project_id"], settings["staging_dataset"], source["staging_table"]]
)

load_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    schema=[
        bigquery.SchemaField("id", "STRING"),
        bigquery.SchemaField("model_a", "STRING"),
        bigquery.SchemaField("model_b", "STRING"),
        bigquery.SchemaField("winner", "STRING"),
    ],
)

with (project_folder / source["path"]).open("rb") as sample_file:
    job = client.load_table_from_file(sample_file, destination, job_config=load_config)
    job.result()

print(f"{client.get_table(destination).num_rows} rows in {destination}")