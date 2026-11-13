import json, glob, os
import pandas as pd

files = sorted(glob.glob("data/openrouter/models_*.json"))
path = files[-1]
snapshot = os.path.basename(path)[len("models_"):-len(".json")]
payload = json.load(open(path, encoding="utf-8"))
df = pd.json_normalize(payload["data"])

keep = {
    "id": "model_id",
    "canonical_slug": "canonical_slug",
    "name": "name",
    "created": "created_unix",
    "context_length": "context_length",
    "hugging_face_id": "hugging_face_id",
    "pricing.prompt": "prompt_usd_per_token",
    "pricing.completion": "completion_usd_per_token",
}
out = df[[c for c in keep if c in df.columns]].rename(columns=keep)

out["prompt_usd_per_m"] = pd.to_numeric(out["prompt_usd_per_token"], errors="coerce") * 1_000_000
out["completion_usd_per_m"] = pd.to_numeric(out["completion_usd_per_token"], errors="coerce") * 1_000_000
out["is_free_variant"] = out["model_id"].str.endswith(":free")
out["is_batch_variant"] = out["model_id"].str.endswith(":batch")
out["created_date"] = pd.to_datetime(out["created_unix"], unit="s").dt.date
out["snapshot_date"] = snapshot

os.makedirs("data/processed", exist_ok=True)
out_path = f"data/processed/openrouter_prices_{snapshot}.csv"
out.to_csv(out_path, index=False)

print(len(out), "models in snapshot", snapshot)
print("saved", out_path)
print(out.sort_values("prompt_usd_per_m", ascending=False)
        [["model_id", "prompt_usd_per_m", "completion_usd_per_m"]].head(5))
