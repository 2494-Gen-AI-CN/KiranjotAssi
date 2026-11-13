import json

import pytest
import ingest_arena as arena


@pytest.fixture
def battle():
    return {
        "id": "vote-1", "model_a": "model-a", "model_b": "model-b",
        "winner": "model_a", "timestamp": "2025-06-20T10:00:00-04:00",
        "language": "en", "is_code": False,
        "category_tag": {"math_v0.1": {"math": True}},
        "conv_metadata": {"sum_assistant_a_tokens": 120,
                          "header_count_a": {"h1": 1, "h2": 2}},
        "source_shard": "sample.parquet",
    }


def test_normalizes_and_flattens_battle(battle):
    battle.update(model_a=" model-a ", winner=" MODEL_A ", language=" en ")
    row, reason = next(arena.clean_batch([battle], set(), "run-1"))
    assert reason is None
    assert row["model_a"] == "model-a"
    assert row["winner"] == "model_a"
    assert row["language"] == "en"
    assert row["timestamp"] == "2025-06-20T14:00:00.000000+00:00"
    assert row["answer_tokens_a"] == 120
    assert row["header_count_a"] == 3
    assert row["answer_tokens_b"] is None
    assert json.loads(row["category_tag_json"]) == battle["category_tag"]
    assert row["run_id"] == "run-1"


@pytest.mark.parametrize("field,value,reason", [
    ("id", " ", "missing or invalid"),
    ("timestamp", "not-a-date", "invalid timestamp"),
    ("winner", "unknown", "unrecognized winner"),
    ("model_b", "model-a", "self-match"),
    ("is_code", "false", "must be boolean"),
    ("language", 42, "must be text"),
    ("conv_metadata", [], "must be an object"),
    ("category_tag", [], "must be an object"),
])
def test_rejects_invalid_battles(battle, field, value, reason):
    battle[field] = value
    row, error = next(arena.clean_batch([battle], set(), "run-1"))
    assert row is None
    assert reason in error


@pytest.mark.parametrize("value", [-1, 1.5, True])
def test_rejects_invalid_token_counts(battle, value):
    battle["conv_metadata"]["sum_assistant_a_tokens"] = value
    row, error = next(arena.clean_batch([battle], set(), "run-1"))
    assert row is None
    assert "non-negative integer" in error


def test_duplicate_detected_across_batches(battle):
    seen = set()
    assert next(arena.clean_batch([battle], seen, "run"))[1] is None
    row, error = next(arena.clean_batch([battle], seen, "run"))
    assert row is None
    assert error == "duplicate vote id"


def test_rejected_id_can_be_corrected(battle):
    seen = set()
    invalid = dict(battle, winner="unknown")
    assert next(arena.clean_batch([invalid], seen, "run"))[0] is None
    assert next(arena.clean_batch([battle], seen, "run"))[1] is None


def test_file_outputs_counts_and_reject_context(tmp_path, battle):
    source = tmp_path / "battles.jsonl"
    source.write_text(json.dumps(battle) + "\ninvalid-json\n" + json.dumps(battle), encoding="utf-8")
    good, bad = tmp_path / "good.jsonl", tmp_path / "bad.jsonl"
    counts = arena.Counts()
    arena.prepare_files([source], good, bad, "run", counts)
    assert (counts.rows_read, counts.rows_accepted, counts.rows_rejected) == (3, 1, 2)
    assert len(good.read_text().splitlines()) == 1
    rejects = [json.loads(line) for line in bad.read_text().splitlines()]
    assert {row["line_number"] for row in rejects} == {2, 3}
    assert all(row["source_file"] == "battles.jsonl" for row in rejects)
