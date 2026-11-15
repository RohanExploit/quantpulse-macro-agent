"""Keyless live market & macro sensors: Frankfurter ECB FX, CoinGecko, HN Algolia."""

from __future__ import annotations

from typing import Any

import requests

HEADERS = {"User-Agent": "QuantPulse-Macro-Agent/1.0"}


def fetch_fx_basket(base: str = "USD", timeout: float = 5.0) -> dict[str, Any]:
    """Fetch live European Central Bank FX rates from Frankfurter API."""
    try:
        resp = requests.get(
            "https://api.frankfurter.app/latest",
            params={"from": base, "to": "INR,EUR,GBP,JPY"},
            headers=HEADERS,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return {"base": base, "date": data.get("date", ""), "rates": data.get("rates", {}), "source": "live-frankfurter-ecb"}
    except Exception as exc:
        return {
            "base": base,
            "date": "fallback",
            "rates": {"INR": 84.4, "EUR": 0.94, "GBP": 0.79, "JPY": 153.2},
            "source": f"fx-backup ({type(exc).__name__})",
        }


def fetch_crypto_series(coin_id: str = "bitcoin", days: int = 30, timeout: float = 6.0) -> dict[str, Any]:
    """Fetch 30-day daily price series from CoinGecko public API."""
    try:
        resp = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
            params={"vs_currency": "usd", "days": days, "interval": "daily"},
            headers=HEADERS,
            timeout=timeout,
        )
        resp.raise_for_status()
        raw_prices = resp.json().get("prices", [])
        prices = [float(p[1]) for p in raw_prices if len(p) >= 2]
        if len(prices) < 5:
            raise ValueError("Insufficient points")
        return {"coin": coin_id, "prices": prices, "source": "live-coingecko"}
    except Exception as exc:
        # Deterministic synthetic random-walk backup if CoinGecko rate-limits
        seed = sum(ord(c) for c in coin_id)
        base = 88000.0 if coin_id == "bitcoin" else (3100.0 if coin_id == "ethereum" else 195.0)
        prices = [round(base * (1.0 + 0.015 * ((i * seed % 7) - 3) / 3.0), 2) for i in range(30)]
        return {"coin": coin_id, "prices": prices, "source": f"coingecko-backup ({type(exc).__name__})"}


def fetch_macro_headlines(query: str = "inflation OR bitcoin OR federal reserve", limit: int = 8, timeout: float = 4.5) -> dict[str, Any]:
    """Fetch live fintech/macro story signals from Hacker News Algolia."""
    try:
        resp = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": query, "tags": "story", "hitsPerPage": limit},
            headers=HEADERS,
            timeout=timeout,
        )
        resp.raise_for_status()
        items = [
            {
                "id": str(h.get("objectID", "")),
                "title": (h.get("title") or "Macro Story")[:110],
                "points": int(h.get("points") or 0),
                "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID', '')}",
            }
            for h in resp.json().get("hits", [])
        ]
        return {"headlines": items, "source": "live-hn-algolia"}
    except Exception as exc:
        return {"headlines": [], "source": f"hn-backup ({type(exc).__name__})"}
