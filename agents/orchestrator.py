"""Lead QuantPulse Macro Strategist orchestrating FX, Quant, Sentiment & Risk-Parity agents."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .llm_router import SynthesisResult, synthesize_with_fallback
from .memory import RegimeMemoryStore
from .subagents import (
    MacroFXLiquidityScout,
    QuantContext,
    QuantitativeRegimeEngine,
    RiskParityAllocatorAgent,
    SentimentDivergenceCritic,
)


def _universal_quant_fallback(ctx: QuantContext) -> str:
    top_a = ctx.metrics_rows[0] if ctx.metrics_rows else {}
    usd_inr = ctx.fx_basket.get("rates", {}).get("INR", "N/A")
    return (
        f"### QuantPulse Macro Regime Briefing (`{ctx.regime}`)\n"
        f"- **FX & Liquidity Anchor**: `USD/INR = {usd_inr}` | Lead tracked asset `{top_a.get('asset', 'BTC')}` at `${top_a.get('spot_usd', 0):,.2f}` (`{top_a.get('return_30d_pct', 0):+.1f}%` 30D, RSI `{top_a.get('rsi_14', 50)}`).\n"
        f"- **Sentiment Critique**: {ctx.divergence_note} (Index `{ctx.sentiment_score:+.1f}`).\n"
        f"- **Educational Allocation Tilt**: `{ctx.allocations[0]['weight_pct']}%` Cash Buffer + inverse-volatility risk-parity weights across tracked assets *(simulation only, not financial advice)*."
    )


class QuantPulseStrategist:
    """Goal-Based + Model-Based + Utility-Based Macro Quant Agent."""

    def __init__(self, memory_store: RegimeMemoryStore | None = None) -> None:
        self.memory = memory_store or RegimeMemoryStore()
        self.subagents = [
            MacroFXLiquidityScout(),
            QuantitativeRegimeEngine(),
            SentimentDivergenceCritic(),
            RiskParityAllocatorAgent(),
        ]

    def run_analysis(
        self,
        coins: list[str] | None = None,
        gemini_key: str | None = None,
        groq_key: str | None = None,
    ) -> dict[str, Any]:
        assets = coins or ["bitcoin", "ethereum", "solana"]
        state = self.memory.load()
        ctx = QuantContext(coins=assets, seen_headline_ids=set(state.get("seen_headline_ids", [])))
        ctx.emit(
            "QuantPulse Strategist",
            "MacroFXLiquidityScout",
            "DELEGATE",
            f"Initiating multi-asset regime, FX & sentiment arbitrage cycle for {', '.join(assets)}.",
            confidence=0.98,
        )

        for agent in self.subagents:
            agent.run(ctx)

        avg_vol = sum(r["ann_vol_pct"] for r in ctx.metrics_rows) / max(len(ctx.metrics_rows), 1)
        usd_inr = float(ctx.fx_basket.get("rates", {}).get("INR", 84.0))

        prompt = (
            f"You are QuantPulse Macro Strategist. Summarize this market regime in 3 crisp educational quant bullets "
            f"(Regime & Volatility, Divergence Signal, Risk-Parity Tilt) under 110 words. State educational simulation only.\n"
            f"Regime: {ctx.regime}\nMetrics: {ctx.metrics_rows}\nDivergence: {ctx.divergence_note}\nAllocations: {ctx.allocations}"
        )
        synthesis: SynthesisResult = synthesize_with_fallback(
            prompt=prompt,
            system_instruction="Be analytical, quantitative, and clearly state educational simulation only.",
            universal_fallback_fn=lambda: _universal_quant_fallback(ctx),
            gemini_key=gemini_key,
            groq_key=groq_key,
        )

        updated_state = self.memory.update_after_run(
            regime=ctx.regime,
            vol_pct=avg_vol,
            usd_inr=usd_inr,
            headline_ids=[h["id"] for h in ctx.headlines if h.get("id")],
            summary=synthesis.text,
        )

        return {
            "regime": ctx.regime,
            "fx_basket": ctx.fx_basket,
            "series_map": ctx.series_map,
            "metrics_rows": ctx.metrics_rows,
            "sentiment_score": ctx.sentiment_score,
            "divergence_note": ctx.divergence_note,
            "headlines": ctx.headlines,
            "allocations": ctx.allocations,
            "messages": [asdict(m) for m in ctx.messages],
            "synthesis": asdict(synthesis),
            "memory": updated_state,
        }
