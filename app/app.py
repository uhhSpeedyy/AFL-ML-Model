from __future__ import annotations

import hmac
import os
import threading
import time
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from afl_ml.artifacts import load_json
from afl_ml.database import database_health, load_predictions
from afl_ml.settings import Settings


load_dotenv()

MELBOURNE = ZoneInfo("Australia/Melbourne")
REFRESH_LOCK = threading.Lock()

TEAM_COLOURS = {
    "Adelaide": ("#0b2341", "#f6c343"),
    "Brisbane Lions": ("#7c1734", "#f2b544"),
    "Carlton": ("#102a43", "#e9f2f8"),
    "Collingwood": ("#111111", "#f5f5f2"),
    "Essendon": ("#171717", "#df2e38"),
    "Fremantle": ("#37225f", "#f4f2f7"),
    "Geelong": ("#142a4a", "#f4f4ee"),
    "Gold Coast": ("#d9292f", "#f7c840"),
    "GWS": ("#e26b20", "#222222"),
    "Hawthorn": ("#4b2b25", "#f5b942"),
    "Melbourne": ("#152b4e", "#d92c3a"),
    "North Melbourne": ("#1f5ba8", "#f4f7fb"),
    "Port Adelaide": ("#111111", "#27a7ad"),
    "Richmond": ("#161616", "#f4c542"),
    "St Kilda": ("#d72638", "#161616"),
    "Sydney": ("#d9292f", "#f6f3eb"),
    "West Coast": ("#123b76", "#f2c84b"),
    "Western Bulldogs": ("#1f53a0", "#d9283d"),
}


def _team_initials(team: str) -> str:
    special = {
        "Brisbane Lions": "BL",
        "Gold Coast": "GC",
        "North Melbourne": "NM",
        "Port Adelaide": "PA",
        "St Kilda": "SK",
        "West Coast": "WC",
        "Western Bulldogs": "WB",
    }
    if team in special:
        return special[team]
    return "".join(word[0] for word in team.split()[:2]).upper()


def _display_time(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(MELBOURNE).strftime("%a %-d %b · %-I:%M %p")


def _margin_phrase(value: float, home_team: str, away_team: str) -> str:
    if abs(float(value)) < 0.5:
        return "Level"
    winner = home_team if float(value) > 0 else away_team
    return f"{winner} by {abs(float(value)):.0f}"


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or Settings()
    app = Flask(__name__)
    app.config["SETTINGS"] = settings

    @lru_cache(maxsize=1)
    def model_report() -> dict:
        return load_json(settings.report_path, default={})

    @lru_cache(maxsize=2)
    def _prediction_payload_cached(_minute_bucket: int) -> tuple[dict, str]:
        if settings.database_enabled and settings.db_server:
            try:
                stored = load_predictions(settings)
                if stored:
                    return stored, "Azure SQL"
            except Exception:
                app.logger.warning("Azure SQL unavailable; serving the bundled snapshot")
        return load_json(
            settings.predictions_path,
            default={"round_name": "Predictions pending", "predictions": []},
        ), "model snapshot"

    def prediction_payload() -> tuple[dict, str]:
        return _prediction_payload_cached(int(time.monotonic() // 60))

    @app.context_processor
    def template_helpers() -> dict:
        return {
            "team_initials": _team_initials,
            "team_colours": lambda team: TEAM_COLOURS.get(team, ("#26364a", "#f3f6f8")),
            "display_time": _display_time,
            "margin_phrase": _margin_phrase,
        }

    @app.get("/")
    def index():
        payload, storage_source = prediction_payload()
        return render_template(
            "index.html",
            payload=payload,
            predictions=payload.get("predictions", []),
            report=model_report(),
            storage_source=storage_source,
        )

    @app.get("/api/predictions")
    def api_predictions():
        payload, _ = prediction_payload()
        return jsonify(payload)

    @app.get("/api/model")
    def api_model():
        return jsonify(model_report())

    @app.get("/health")
    def health():
        # App Service probes must stay fast and must not keep a serverless SQL
        # database awake. SQL connectivity has its own explicit readiness route.
        payload = load_json(
            settings.predictions_path,
            default={"predictions": []},
        )
        return jsonify(
            {
                "status": "ok",
                "model_version": payload.get("model_version"),
                "predictions": len(payload.get("predictions", [])),
                "database_configured": bool(settings.db_server and settings.db_name),
            }
        )

    @app.get("/ready")
    def ready():
        if not settings.db_server:
            return jsonify({"status": "ready", "database": "snapshot mode"})
        ok, detail = database_health(settings)
        if not ok:
            app.logger.warning("Azure SQL readiness check failed: %s", detail)
        status = 200 if ok else 503
        database_state = "connected" if ok else "unavailable"
        return jsonify({"status": "ready" if ok else "degraded", "database": database_state}), status

    @app.post("/api/admin/refresh")
    def admin_refresh():
        configured = settings.refresh_token
        supplied = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not configured:
            return jsonify({"error": "Prediction refresh is not configured"}), 503
        if not supplied or not hmac.compare_digest(configured, supplied):
            return jsonify({"error": "Unauthorized"}), 401
        if not REFRESH_LOCK.acquire(blocking=False):
            return jsonify({"error": "A refresh is already running"}), 409
        try:
            # The full pandas/scikit-learn stack is needed only by the scheduled
            # refresh, not for normal web requests or container health probes.
            from afl_ml.service import refresh_prediction_snapshot

            result = refresh_prediction_snapshot(
                settings,
                persist_db=True,
                force=True,
            )
            _prediction_payload_cached.cache_clear()
            return jsonify(
                {
                    "status": "refreshed",
                    "round_name": result.get("round_name"),
                    "predictions": len(result.get("predictions", [])),
                    "state_updates_applied": result.get("state_updates_applied", 0),
                }
            )
        finally:
            REFRESH_LOCK.release()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
