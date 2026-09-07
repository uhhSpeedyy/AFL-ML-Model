from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path

import pytest

from afl_ml.artifacts import load_json, load_model
from afl_ml.prediction import fixture_feature_frame, generate_predictions


ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"


def test_committed_model_artifacts_load_and_predict():
    bundle = load_model(ARTIFACTS_DIR / "afl_margin_model.joblib")
    report = load_json(ARTIFACTS_DIR / "model_report.json")
    snapshot = load_json(ARTIFACTS_DIR / "predictions.json")

    assert bundle.model_version == report["model_version"] == snapshot["model_version"]
    # An empty next-round snapshot is valid after the grand final. Continue
    # exercising model inference with a synthetic fixture in that case.
    saved_fixture = snapshot["predictions"][0] if snapshot["predictions"] else {
        "game_id": "test-fixture", "season": 2026, "round_number": 30,
        "round_name": "Test fixture", "start_time": datetime(2026, 10, 1, tzinfo=timezone.utc).isoformat(),
        "venue": "M.C.G.", "home_team": "Geelong", "away_team": "Brisbane Lions",
    }
    game = {
        "id": saved_fixture["game_id"],
        "year": saved_fixture["season"],
        "round": saved_fixture["round_number"],
        "roundname": saved_fixture["round_name"],
        "start_time": datetime.fromisoformat(saved_fixture["start_time"]),
        "venue": saved_fixture["venue"],
        "hteam": saved_fixture["home_team"],
        "ateam": saved_fixture["away_team"],
        "is_final": False,
    }

    frame = fixture_feature_frame(bundle, [game])
    model_output = bundle.predict(frame)
    values = {
        key: float(result[0])
        for key, result in model_output.items()
    }
    assert all(math.isfinite(value) for value in values.values())

    probabilities = [
        values["home_probability"],
        values["away_probability"],
        values["draw_probability"],
    ]
    assert all(0.0 <= probability <= 1.0 for probability in probabilities)
    assert sum(probabilities) == pytest.approx(1.0, abs=1e-12)

    payload = generate_predictions(bundle, [game])
    prediction = payload["predictions"][0]
    assert payload["model_version"] == bundle.model_version
    assert prediction["model_version"] == bundle.model_version
    assert all(
        math.isfinite(float(prediction[key]))
        for key in (
            "home_win_probability",
            "away_win_probability",
            "draw_probability",
            "expected_home_margin",
            "interval_80_low",
            "interval_80_high",
        )
    )
