from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load_schema(name: str) -> dict:
    with (SCHEMAS / name).open() as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return schema


def validate(name: str, instance: dict) -> None:
    Draft202012Validator(load_schema(name)).validate(instance)


def valid_review_record() -> dict:
    return {
        "schema_version": "0.1",
        "review_id": "rev_1",
        "packet_id": "pkt_1",
        "effect_id": "effect_1",
        "review_decision": "approved",
        "reviewer_type": "main_agent",
        "reviewed_at": "2026-05-23T12:00:00Z",
        "execution_status": "not_executed",
    }


def test_valid_approved_side_effect_review_record_schema_passes():
    validate("side-effect-review-record.schema.json", valid_review_record())


def test_valid_denied_side_effect_review_record_schema_passes():
    record = {
        **valid_review_record(),
        "review_decision": "denied",
        "reviewer_type": "policy",
        "notes_digest": "sha256:" + "b" * 64,
    }

    validate("side-effect-review-record.schema.json", record)


@pytest.mark.parametrize("field", [
    "result",
    "execution_result",
    "payload",
    "approved_by",
    "executed_at",
])
def test_side_effect_review_record_schema_rejects_raw_result_payload_and_execution_state(field: str):
    record = {**valid_review_record(), field: "must not be present"}

    with pytest.raises(ValidationError, match=field):
        validate("side-effect-review-record.schema.json", record)


@pytest.mark.parametrize("field", [
    "review_id",
    "packet_id",
    "effect_id",
    "review_decision",
    "reviewer_type",
    "reviewed_at",
    "execution_status",
])
def test_side_effect_review_record_schema_rejects_missing_required_fields(field: str):
    record = valid_review_record()
    del record[field]

    with pytest.raises(ValidationError, match=field):
        validate("side-effect-review-record.schema.json", record)


def test_side_effect_review_record_schema_rejects_invalid_enums():
    record = {**valid_review_record(), "review_decision": "rubber_stamped"}

    with pytest.raises(ValidationError, match="rubber_stamped"):
        validate("side-effect-review-record.schema.json", record)


def test_side_effect_review_record_python_api_round_trips_schema_valid_dict():
    from sovereignty import SideEffectReviewRecord

    record = SideEffectReviewRecord.from_dict(valid_review_record())

    assert record.to_dict() == valid_review_record()
    validate("side-effect-review-record.schema.json", record.to_dict())


def test_side_effect_review_record_rejects_invalid_digest():
    from sovereignty import SideEffectReviewRecord, SovereigntyPolicyError

    record = {**valid_review_record(), "result_digest": "raw result text"}

    with pytest.raises(SovereigntyPolicyError, match="result_digest"):
        SideEffectReviewRecord.from_dict(record)
