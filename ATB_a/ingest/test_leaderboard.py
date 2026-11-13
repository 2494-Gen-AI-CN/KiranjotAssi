import json

import pytest
import ingest_leaderboard as leaderboard


@pytest.fixture
def entry():
    return {"model_name": " model-a ", "leaderboard_publish_date": "2025-07-17",
            "leaderboard_variant": "text", "category": "overall", "rank": "2",
            "rating": "1400.5", "vote_count": "200", "organization": "Example",
            "license": "proprietary"}


def test_clean_entry_converts_types(entry):
    row = leaderboard.clean_leaderboard(entry, "2025-07-17", "text")
    assert row["model_name"] == "model-a"
    assert row["rank"] == 2
    assert row["rating"] == 1400.5
    assert row["vote_count"] == 200
    assert row["rating_lower"] is None


@pytest.mark.parametrize("field,value", [("rank", 0), ("rank", 1.5),
    ("vote_count", -1), ("rating", "NaN"), ("rating", "Infinity"), ("model_name", " ")])
def test_invalid_entry_rejected(entry, field, value):
    entry[field] = value
    with pytest.raises(ValueError):
        leaderboard.clean_leaderboard(entry, "2025-07-17", "text")


def test_file_filtering_duplicates_and_dates(tmp_path, entry):
    rows = [entry, entry, dict(entry, category="coding"),
            dict(entry, leaderboard_publish_date="2025-02-30")]
    path = tmp_path / "text.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    good, bad = tmp_path / "good.jsonl", tmp_path / "bad.jsonl"
    counts = leaderboard.Counts()
    leaderboard.prepare_group(tmp_path, [{"path": path.name, "leaderboard_variant": "text"}], good, bad, "run", counts)
    assert (counts.rows_read, counts.rows_accepted, counts.rows_rejected, counts.rows_filtered) == (4, 1, 2, 1)
    reasons = [json.loads(line)["reason"] for line in bad.read_text().splitlines()]
    assert "duplicate source key" in reasons
    assert any("valid YYYY-MM-DD" in reason for reason in reasons)


def test_same_model_and_date_allowed_in_different_variants(tmp_path, entry):
    sources = []
    for variant in ("text", "text_style_control"):
        path = tmp_path / f"{variant}.jsonl"
        path.write_text(json.dumps(dict(entry, leaderboard_variant=variant)), encoding="utf-8")
        sources.append({"path": path.name, "leaderboard_variant": variant})
    counts = leaderboard.Counts()
    leaderboard.prepare_group(tmp_path, sources, tmp_path / "good", tmp_path / "bad", "run", counts)
    assert counts.rows_accepted == 2
    assert counts.rows_rejected == 0
