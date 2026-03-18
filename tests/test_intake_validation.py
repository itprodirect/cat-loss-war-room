"""Tests for strict case intake ingestion and schema validation."""

import json
from pathlib import Path

import pytest

from war_room.query_plan import (
    CASE_INTAKE_OPTIONAL_FIELDS,
    CASE_INTAKE_REQUIRED_FIELDS,
    IntakeValidationError,
    load_case_intake,
    validate_case_intake_payload,
)


def _valid_payload() -> dict:
    return {
        "event_name": "Hurricane Milton",
        "event_date": "2024-10-09",
        "state": "FL",
        "county": "Pinellas",
        "carrier": "Citizens Property Insurance",
        "policy_type": "HO-3 Dwelling",
        "posture": ["denial", "bad_faith"],
        "key_facts": [
            "Roof damage and water intrusion reported within 48 hours",
        ],
        "coverage_issues": ["wind_vs_water_causation"],
    }


def test_schema_field_lists_match_documented_contract():
    assert CASE_INTAKE_REQUIRED_FIELDS == (
        "event_name",
        "event_date",
        "state",
        "county",
        "carrier",
        "policy_type",
    )
    assert CASE_INTAKE_OPTIONAL_FIELDS == (
        "posture",
        "key_facts",
        "coverage_issues",
    )


def test_validate_case_intake_payload_accepts_valid_payload():
    intake = validate_case_intake_payload(_valid_payload())

    assert intake.event_name == "Hurricane Milton"
    assert intake.event_date == "2024-10-09"
    assert intake.posture == ["denial", "bad_faith"]


def test_validate_case_intake_payload_defaults_posture_when_missing():
    payload = _valid_payload()
    payload.pop("posture")

    intake = validate_case_intake_payload(payload)

    assert intake.posture == ["denial"]


def test_validate_case_intake_payload_rejects_missing_required_fields():
    payload = _valid_payload()
    payload.pop("carrier")

    with pytest.raises(IntakeValidationError, match=r"Missing required field\(s\): carrier"):
        validate_case_intake_payload(payload)


def test_validate_case_intake_payload_rejects_unknown_fields():
    payload = _valid_payload()
    payload["claim_number"] = "12345"

    with pytest.raises(IntakeValidationError, match=r"Unexpected field\(s\): claim_number"):
        validate_case_intake_payload(payload)


def test_validate_case_intake_payload_rejects_wrong_field_type():
    payload = _valid_payload()
    payload["policy_type"] = 42

    with pytest.raises(IntakeValidationError, match="Field 'policy_type' must be a non-empty string"):
        validate_case_intake_payload(payload)


def test_validate_case_intake_payload_rejects_invalid_event_date_format():
    payload = _valid_payload()
    payload["event_date"] = "10/09/2024"

    with pytest.raises(IntakeValidationError, match="YYYY-MM-DD"):
        validate_case_intake_payload(payload)


def test_validate_case_intake_payload_rejects_posture_not_list():
    payload = _valid_payload()
    payload["posture"] = "denial,bad_faith"

    with pytest.raises(IntakeValidationError, match="Field 'posture' must be a list"):
        validate_case_intake_payload(payload)


def test_validate_case_intake_payload_rejects_invalid_posture_token():
    payload = _valid_payload()
    payload["posture"] = ["bad faith"]

    with pytest.raises(IntakeValidationError, match="must use snake_case tokens"):
        validate_case_intake_payload(payload)


def test_load_case_intake_reads_json_and_validates(tmp_path: Path):
    intake_path = tmp_path / "intake.json"
    intake_path.write_text(json.dumps(_valid_payload(), indent=2), encoding="utf-8")

    intake = load_case_intake(intake_path)

    assert intake.county == "Pinellas"


def test_load_case_intake_rejects_invalid_json(tmp_path: Path):
    intake_path = tmp_path / "bad.json"
    intake_path.write_text("{ not valid json", encoding="utf-8")

    with pytest.raises(IntakeValidationError, match="Invalid JSON in intake file"):
        load_case_intake(intake_path)

def test_committed_eval_intakes_validate_against_canonical_schema():
    intakes_dir = Path(__file__).resolve().parent.parent / "eval" / "intakes"
    intake_paths = sorted(path for path in intakes_dir.glob("*.json"))

    assert len(intake_paths) >= 3
    assert any(path.name == "tx_hail_allstate_tarrant_dp3.json" for path in intake_paths)

    for intake_path in intake_paths:
        intake = load_case_intake(intake_path)
        assert intake.event_name
        assert intake.state
        assert intake.carrier
