"""Automated pytest suite for QuantPulse Macro multi-agent quant strategist."""

from __future__ import annotations

from pathlib import Path

from agents.memory import RegimeMemoryStore
from agents.orchestrator import QuantPulseStrategist
from agents.subagents import compute_rsi_14


def test_rsi_bounds() -> None:
    up = [100 + i for i in range(20)]
    down = [120 - i for i in range(20)]
    assert compute_rsi_14(up) == 100.0
    assert compute_rsi_14(down) == 0.0


def test_regime_memory_deduplicates_headlines(tmp_path: Path) -> None:
    store = RegimeMemoryStore(tmp_path / "reg.json")
    s1 = store.update_after_run("RISK-ON EXPANSION", 45.0, 84.2, ["h1", "h2"], "ok")
    s2 = store.update_after_run("VOLATILE CHOP", 62.0, 84.3, ["h2", "h3"], "ok2")
    assert s1["seen_headline_ids"] == ["h1", "h2"]
    assert s2["seen_headline_ids"] == ["h1", "h2", "h3"]


def test_full_analysis_mocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "agents.subagents.fetch_fx_basket",
        lambda base="USD": {"base": "USD", "date": "2026-11-15", "rates": {"INR": 84.5, "EUR": 0.94, "GBP": 0.79, "JPY": 152.0}, "source": "mock"},
    )
    monkeypatch.setattr(
        "agents.subagents.fetch_crypto_series",
        lambda coin, days=30: {"coin": coin, "prices": [100.0 + i * 1.2 for i in range(30)], "source": "mock"},
    )
    monkeypatch.setattr(
        "agents.subagents.fetch_macro_headlines",
        lambda: {"headlines": [{"id": "10", "title": "ETF adoption growth rally", "points": 90, "url": "https://hn.algolia.com"}], "source": "mock"},
    )
    out = QuantPulseStrategist(RegimeMemoryStore(tmp_path / "reg.json")).run_analysis(["bitcoin", "ethereum"], gemini_key="", groq_key="")
    assert round(sum(a["weight_pct"] for a in out["allocations"]), 0) == 100.0
    assert len(out["messages"]) == 5
