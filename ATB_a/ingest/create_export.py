"""convert Arena parquet file format to JSONL file format"""

import json
from pathlib import Path
import pyarrow.parquet as pq

# dataset columns as they will be in the parquet file
# extract neccessary columns
COLUMNS = ["id", "timestamp", "model_a", "model_b", "winner", "language", "is_code", 
           "category_tag", "conv_metadata"]

# find the file and prepare output'
# parquet file dir and the path to json directory
def export_arena(source_dir, destination):
    # sort every parquet file in the folder by file name
    shards = sorted(source_dir.glob("*.parquet"))

    # raise error since sorted() returns empty instance if fails
    if not shards:
        raise FileNotFoundError(f"No Parquet shards in {source_dir}")

    # create output folder
    destination.parent.mkdir(parents=True, exist_ok=True)
    # create a temp to handle failed exports from overwritting 
    temporary = destination.with_suffix(".tmp")
    count = 0
    
    with temporary.open("w", encoding="utf-8") as output:
        for shard in shards: # loop 7 pq files
            source = pq.ParquetFile(shard) # open pq file
            missing = set(COLUMNS) - set(source.schema_arrow.names)
            if missing:
                raise ValueError(f"{shard.name} is missing {sorted(missing)}")

            # convert the rows into JSON
            # read 5k vote per batch 
            for batch in source.iter_batches(batch_size=5000, columns=COLUMNS):
                for row in batch.to_pylist(): # convert batch into python dictionaries
                    if row["timestamp"] is not None:
                        row["timestamp"] = row["timestamp"].isoformat()
                    row["source_shard"] = shard.name
                    # convert python dictionary into JSONL
                    output.write(json.dumps(row, ensure_ascii=False) + "\n")
                count += batch.num_rows

    temporary.replace(destination)
    return count


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    destination = root / "data/processed/arena_battles.jsonl"
    count = export_arena(root / "data/raw/arena-140k/data", destination)
    print(f"Exported {count:,} Arena votes to {destination}")
            
