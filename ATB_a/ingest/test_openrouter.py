import csv
import json
from decimal import Decimal

import pytest
import ingest_openrouter as prices


@pytest.fixture
def price_row():
    return {"model_id": " provider/model ", "snapshot_date": "2026-11-08",
            "prompt_usd_per_m": "0.15", "completion_usd_per_m": "0.60",
            "context_length": "128000", "is_free_variant": " FALSE ",
            "is_batch_variant": "false"}


def test_clean_price_converts_types(price_row):
    row = prices.clean_price(price_row, "2026-11-08")
    assert row["model_id"] == "provider/model"
    assert row["context_length"] == 128000
    assert row["is_free_variant"] is False
    assert Decimal(row["prompt_usd_per_m"]) == Decimal("0.15")


@pytest.mark.parametrize("value", [None, "", "-1000000"])
def test_missing_prices_become_null(value):
    assert prices.price(value, "price") is None


@pytest.mark.parametrize("value", ["-0.01", "NaN", "Infinity", "1e29", "abc"])
def test_invalid_prices_rejected(value):
    with pytest.raises(ValueError):
        prices.price(value, "price")


def test_price_rounds_float_artifacts():
    assert prices.price("0.30000000000000004", "price") == "0.300000000"


@pytest.mark.parametrize("value", ["yes", 1, None])
def test_invalid_boolean_rejected(value):
    with pytest.raises(ValueError, match="true or false"):
        prices.boolean(value, "is_free_variant")


def test_csv_rejects_duplicate_and_invalid_date(tmp_path, price_row):
    path = tmp_path / "prices.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=price_row.keys())
        writer.writeheader()
        writer.writerows([price_row, price_row, dict(price_row, snapshot_date="2026-02-30")])
    good, bad = tmp_path / "good.jsonl", tmp_path / "bad.jsonl"
    counts = prices.Counts()
    prices.prepare_group(tmp_path, [{"path": path.name}], good, bad, "run", counts)
    assert (counts.rows_read, counts.rows_accepted, counts.rows_rejected) == (3, 1, 2)
    reasons = [json.loads(line)["reason"] for line in bad.read_text().splitlines()]
    assert "duplicate source key" in reasons
    assert any("valid YYYY-MM-DD" in reason for reason in reasons)
