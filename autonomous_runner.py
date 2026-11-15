"""Headless autonomous runner for scheduled QuantPulse macro regime snapshots."""

from __future__ import annotations

import json

from agents.orchestrator import QuantPulseStrategist


def main() -> None:
    res = QuantPulseStrategist().run_analysis()
    print(
        json.dumps(
            {
                "regime": res["regime"],
                "usd_inr": res["fx_basket"].get("rates", {}).get("INR"),
                "sentiment_score": res["sentiment_score"],
                "provider": res["synthesis"]["provider"],
                "total_runs": res["memory"]["total_runs"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
