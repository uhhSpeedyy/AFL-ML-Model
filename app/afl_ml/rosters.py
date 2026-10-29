from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_roster_changes(path: Path) -> dict[str, Any] | None:
    """Load a versioned, human-auditable off-season roster overlay."""
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("clubs"), dict):
        raise ValueError(f"Invalid roster file: {path}")
    return payload


def roster_summary(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None
    clubs = payload.get("clubs", {})
    return {
        "season": int(payload["season"]),
        "as_of": str(payload["as_of"]),
        "as_of_label": str(payload.get("as_of_label", payload["as_of"])),
        "status": str(payload.get("status", "provisional")),
        "clubs_updated": len(clubs),
        "confirmed_ins": sum(len(change.get("ins", [])) for change in clubs.values()),
        "confirmed_outs": sum(
            1
            for change in clubs.values()
            for player in change.get("outs", [])
            if not player.get("retained", False)
        ),
        "note": str(payload.get("note", "")),
        "sources": list(payload.get("sources", [])),
    }
