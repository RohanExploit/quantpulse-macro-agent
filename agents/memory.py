"""Model-based persistent memory for QuantPulse Macro regime transitions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_STATE: dict[str, Any] = {
    "agent_name": "QuantPulse Macro Strategist",
    "regime_history": [],
    "seen_headline_ids": [],
    "total_runs": 0,
    "last_run_utc": None,
}


class RegimeMemoryStore:
    """Persists macro regime transitions and deduplicated headline IDs."""

    def __init__(self, state_path: Path | str | None = None) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        self.path = Path(state_path) if state_path else base_dir / "state" / "regime_memory.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return json.loads(json.dumps(DEFAULT_STATE))
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for key, val in DEFAULT_STATE.items():
                data.setdefault(key, json.loads(json.dumps(val)))
            return data
        except Exception:
            return json.loads(json.dumps(DEFAULT_STATE))

    def save(self, state: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def update_after_run(
        self,
        regime: str,
        vol_pct: float,
        usd_inr: float,
        headline_ids: list[str],
        summary: str,
    ) -> dict[str, Any]:
        state = self.load()
        seen = set(state.get("seen_headline_ids", []))
        new_ids = [hid for hid in headline_ids if hid not in seen]
        state["seen_headline_ids"] = (state.get("seen_headline_ids", []) + new_ids)[-200:]

        now_iso = datetime.now(timezone.utc).isoformat()
        state["total_runs"] = int(state.get("total_runs", 0)) + 1
        state["last_run_utc"] = now_iso
        state["regime_history"].append(
            {
                "timestamp_utc": now_iso,
                "regime": regime,
                "annualized_vol_pct": round(vol_pct, 2),
                "usd_inr": round(usd_inr, 3),
                "new_headlines": len(new_ids),
                "summary": summary[:200],
            }
        )
        state["regime_history"] = state["regime_history"][-30:]
        self.save(state)
        return state
