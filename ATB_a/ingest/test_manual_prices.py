import json
from decimal import Decimal

import pytest
import ingest_manual_prices as manual


@pytest.fixture
def reference():
    return {"arena_name": "model-a", "prompt_usd_per_m": "2", "completion_usd_per_m": "8",
            "provider": "Example", "pricing_terms": "Standard text API",
            "price_status": "provider_rate", "source_url": "https://example.com/pricing",
            "checked_on": "2026-11-08"}


def test_recomputes_blended_price(reference):
    reference["blended_price_per_m"] = "999"
    row = manual.clean_row(reference)
    assert Decimal(row["blended_price_per_m"]) == Decimal("5")
    assert row["price_status"] == "provider_rate"


@pytest.mark.parametrize("field", ["provider", "source_url", "pricing_terms"])
def test_missing_evidence_is_flagged(reference, field):
    reference[field] = None
    assert manual.clean_row(reference)["price_status"] == "source_details_missing"


@pytest.mark.parametrize("field,value", [("prompt_usd_per_m", "-1"),
    ("completion_usd_per_m", "NaN"), ("source_url", "file:///tmp/prices"),
    ("checked_on", "2026-02-30"), ("price_status", "unverified"), ("arena_name", "")])
def test_invalid_reference_rejected(reference, field, value):
    reference[field] = value
    with pytest.raises(ValueError):
        manual.clean_row(reference)


def test_file_normalization_duplicate_and_audit(tmp_path, reference):
    path = tmp_path / "manual.jsonl"
    padded = dict(reference, arena_name=" model-a ")
    path.write_text(json.dumps(padded) + "\n" + json.dumps(reference), encoding="utf-8")
    good, bad = tmp_path / "good.jsonl", tmp_path / "bad.jsonl"
    counts = manual.prepare_files(tmp_path, [{"path": path.name}], good, bad, "run-1")
    assert counts == (2, 1, 1)
    row = json.loads(good.read_text())
    assert row["arena_name"] == "model-a"
    assert row["run_id"] == "run-1"
    reject = json.loads(bad.read_text())
    assert reject["reason"] == "duplicate Arena model ID"
    assert reject["line_number"] == 2
