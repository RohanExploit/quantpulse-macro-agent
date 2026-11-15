"""Four specialized Quantitative Sub-Agents under QuantPulse Macro Strategist."""

from __future__ import annotations

import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from .tools import fetch_crypto_series, fetch_fx_basket, fetch_macro_headlines

POSITIVE_WORDS = {"rally", "surge", "growth", "breakthrough", "etf", "adoption", "easing", "profit", "bull"}
NEGATIVE_WORDS = {"crash", "recession", "inflation", "hack", "bankrupt", "default", "layoff", "tariff", "rate hike", "slump"}


@dataclass
class QuantBusMessage:
    sender: str
    recipient: str
    phase: str
    content: str
    confidence: float


@dataclass
class QuantContext:
    coins: list[str]
    seen_headline_ids: set[str]
    fx_basket: dict[str, Any] = field(default_factory=dict)
    series_map: dict[str, list[float]] = field(default_factory=dict)
    metrics_rows: list[dict[str, Any]] = field(default_factory=list)
    regime: str = "VOLATILE CHOP"
    sentiment_score: float = 0.0
    divergence_note: str = ""
    headlines: list[dict[str, Any]] = field(default_factory=list)
    allocations: list[dict[str, Any]] = field(default_factory=list)
    messages: list[QuantBusMessage] = field(default_factory=list)

    def emit(self, sender: str, recipient: str, phase: str, content: str, confidence: float = 0.92) -> None:
        self.messages.append(QuantBusMessage(sender, recipient, phase, content, round(confidence, 2)))


def compute_rsi_14(prices: list[float]) -> float:
    """Compute classic 14-period Relative Strength Index."""
    if len(prices) < 15:
        return 50.0
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))][-14:]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_g = sum(gains) / 14.0
    avg_l = sum(losses) / 14.0
    if avg_l == 0:
        return 100.0 if avg_g > 0 else 50.0
    rs = avg_g / avg_l
    return round(100.0 - (100.0 / (1.0 + rs)), 1)


class MacroFXLiquidityScout:
    """Sub-Agent 1: Streams ECB Frankfurter FX rates and 30-day CoinGecko price series in parallel."""

    name = "MacroFXLiquidityScout"

    def run(self, ctx: QuantContext) -> None:
        with ThreadPoolExecutor(max_workers=5) as pool:
            fx_fut = pool.submit(fetch_fx_basket, "USD")
            coin_futs = {coin: pool.submit(fetch_crypto_series, coin, 30) for coin in ctx.coins}
            ctx.fx_basket = fx_fut.result()
            for coin, fut in coin_futs.items():
                ctx.series_map[coin] = fut.result()["prices"]
        usd_inr = ctx.fx_basket.get("rates", {}).get("INR", 0)
        ctx.emit(
            self.name,
            "QuantitativeRegimeEngine",
            "SENSE-MKT",
            f"Ingested live FX basket (USD/INR={usd_inr}) and 30D series for {', '.join(ctx.coins)}.",
            confidence=0.95,
        )


class QuantitativeRegimeEngine:
    """Sub-Agent 2: Computes annualized volatility, RSI-14, max drawdown, and market regime."""

    name = "QuantitativeRegimeEngine"

    def run(self, ctx: QuantContext) -> None:
        rows: list[dict[str, Any]] = []
        for coin, prices in ctx.series_map.items():
            rets = [(prices[i] / prices[i - 1]) - 1.0 for i in range(1, len(prices)) if prices[i - 1] > 0]
            mean_r = sum(rets) / max(len(rets), 1)
            var_r = sum((r - mean_r) ** 2 for r in rets) / max(len(rets), 1)
            ann_vol = round(math.sqrt(var_r) * math.sqrt(365) * 100.0, 1)

            peak = prices[0]
            max_dd = 0.0
            for p in prices:
                peak = max(peak, p)
                dd = ((p - peak) / peak) * 100.0 if peak > 0 else 0.0
                max_dd = min(max_dd, dd)

            ret_30d = round(((prices[-1] / prices[0]) - 1.0) * 100.0, 2) if prices[0] > 0 else 0.0
            rsi = compute_rsi_14(prices)
            rows.append(
                {
                    "asset": coin.upper(),
                    "spot_usd": round(prices[-1], 2),
                    "return_30d_pct": ret_30d,
                    "ann_vol_pct": ann_vol,
                    "rsi_14": rsi,
                    "max_drawdown_pct": round(max_dd, 2),
                }
            )

        ctx.metrics_rows = rows
        avg_ret = sum(r["return_30d_pct"] for r in rows) / max(len(rows), 1)
        avg_vol = sum(r["ann_vol_pct"] for r in rows) / max(len(rows), 1)

        if avg_ret > 4.0 and avg_vol < 65.0:
            ctx.regime = "RISK-ON EXPANSION"
        elif avg_ret < -4.0 or avg_vol >= 75.0:
            ctx.regime = "RISK-OFF DEFENSIVE"
        else:
            ctx.regime = "VOLATILE CHOP"

        ctx.emit(
            self.name,
            "SentimentDivergenceCritic",
            "QUANT-REGIME",
            f"Classified regime={ctx.regime} (mean 30D return={avg_ret:+.1f}%, mean ann. vol={avg_vol:.1f}%).",
            confidence=0.93,
        )


class SentimentDivergenceCritic:
    """Sub-Agent 3: Scores live HN macro/crypto sentiment and flags price-sentiment divergence."""

    name = "SentimentDivergenceCritic"

    def run(self, ctx: QuantContext) -> None:
        hl = fetch_macro_headlines()
        ctx.headlines = hl["headlines"]
        pos, neg = 0, 0
        for h in ctx.headlines:
            t = h["title"].lower()
            pos += sum(1 for w in POSITIVE_WORDS if w in t)
            neg += sum(1 for w in NEGATIVE_WORDS if w in t)

        raw_sent = ((pos - neg) / max(pos + neg, 1)) * 100.0
        ctx.sentiment_score = round(raw_sent, 1)
        avg_ret = sum(r["return_30d_pct"] for r in ctx.metrics_rows) / max(len(ctx.metrics_rows), 1)

        if raw_sent > 20 and avg_ret < -3:
            ctx.divergence_note = "Bearish Price / Bullish Headline Divergence — avoid chasing bounces."
        elif raw_sent < -20 and avg_ret > 3:
            ctx.divergence_note = "Wall-of-Worry Bullish Divergence — price trending up despite cautious media."
        else:
            ctx.divergence_note = "Macro sentiment broadly aligned with realized 30D price momentum."

        ctx.emit(
            self.name,
            "RiskParityAllocatorAgent",
            "CRITIQUE",
            f"Sentiment index={ctx.sentiment_score:+.1f} across {len(ctx.headlines)} headlines. {ctx.divergence_note}",
            confidence=0.89,
        )


class RiskParityAllocatorAgent:
    """Sub-Agent 4: Computes educational inverse-volatility risk-parity weights."""

    name = "RiskParityAllocatorAgent"

    def run(self, ctx: QuantContext) -> None:
        cash_base = 45.0 if "RISK-OFF" in ctx.regime else (30.0 if "CHOP" in ctx.regime else 20.0)
        risk_budget = 100.0 - cash_base
        inv_vols = [1.0 / max(r["ann_vol_pct"], 10.0) for r in ctx.metrics_rows]
        tot_inv = sum(inv_vols) or 1.0

        allocs = [{"bucket": "USD / T-Bill Cash Reserve", "weight_pct": round(cash_base, 1), "rationale": f"Regime buffer ({ctx.regime})"}]
        for row, iv in zip(ctx.metrics_rows, inv_vols):
            w = round((iv / tot_inv) * risk_budget, 1)
            allocs.append({"bucket": row["asset"], "weight_pct": w, "rationale": f"Inverse-vol parity (vol={row['ann_vol_pct']}%, RSI={row['rsi_14']})"})

        ctx.allocations = allocs
        ctx.emit(
            self.name,
            "QuantPulse Strategist",
            "ALLOCATE",
            f"Computed {len(allocs)}-bucket educational risk-parity tilt with {cash_base:.0f}% defensive cash buffer.",
            confidence=0.95,
        )
