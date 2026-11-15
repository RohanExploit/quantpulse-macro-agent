"""QuantPulse Macro — Institutional Quant Desk UI."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from agents.orchestrator import QuantPulseStrategist

st.set_page_config(
    page_title="QuantPulse Macro | Autonomous Regime & Risk-Parity Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; color: #ECFDF5; }
code, pre, .mono { font-family: 'JetBrains Mono', monospace !important; }
.stApp { background: radial-gradient(circle at 85% 5%, #112A1F 0%, #070B09 60%); }
.quant-header {
    background: rgba(15, 23, 19, 0.92);
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 12px;
    padding: 1.2rem 1.45rem;
    margin-bottom: 1rem;
}
.quant-bus {
    background: rgba(15, 23, 19, 0.8);
    border-left: 3px solid #10B981;
    padding: 0.7rem 0.95rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 0.55rem;
}
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Quant Universe")
    selected_coins = st.multiselect("Tracked Crypto Liquidity Benchmarks", ["bitcoin", "ethereum", "solana", "cardano"], default=["bitcoin", "ethereum", "solana"])
    with st.expander("AI Brain Keys (Optional — 90% Keyless)"):
        gemini_key = st.text_input("Gemini API Key Override", type="password")
        groq_key = st.text_input("Groq API Key Override", type="password")
    run_btn = st.button("Compute Macro Regime", type="primary", use_container_width=True)
    st.caption("Educational Quant Simulation Only | Vishal Chavan — BTCOC701")

if "quant_res" not in st.session_state or run_btn:
    with st.spinner("QuantPulse streaming ECB FX, CoinGecko 30D & Macro Sentiment..."):
        st.session_state.quant_res = QuantPulseStrategist().run_analysis(
            coins=selected_coins or ["bitcoin", "ethereum"],
            gemini_key=gemini_key,
            groq_key=groq_key,
        )

res = st.session_state.quant_res
rates = res["fx_basket"].get("rates", {})
reg_color = "#10B981" if "RISK-ON" in res["regime"] else ("#EF4444" if "RISK-OFF" in res["regime"] else "#F59E0B")

st.markdown(
    f"""
<div class="quant-header">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.8rem;">
    <div>
      <h2 style="margin:0; color:#ECFDF5;">QuantPulse Macro — Multi-Asset Regime &amp; Risk-Parity Desk</h2>
      <div style="color:#9CA3AF; margin-top:0.25rem;">Autonomous fusion of ECB Frankfurter FX, CoinGecko 30D Volatility/RSI &amp; Macro Headline Sentiment</div>
    </div>
    <div class="mono" style="border:1px solid {reg_color}; color:{reg_color}; padding:0.35rem 0.8rem; border-radius:8px; font-weight:600;">
      {res['regime']}
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("USD / INR (ECB)", f"₹{rates.get('INR', 'N/A')}")
c2.metric("EUR / USD", f"{round(1 / rates['EUR'], 3) if rates.get('EUR') else 'N/A'}")
c3.metric("Sentiment Index", f"{res['sentiment_score']:+.1f}")
c4.metric("10% AI Layer", res["synthesis"]["provider"])

t1, t2, t3 = st.tabs(["Regime Charts & Risk-Parity", "Sub-Agent Quant Bus", "PEAS & Regime Memory"])

with t1:
    left, right = st.columns([1.3, 1])
    with left:
        st.subheader("Normalized 30-Day Performance Index (Base = 100)")
        fig = go.Figure()
        for coin, prices in res["series_map"].items():
            norm = [(p / prices[0]) * 100.0 for p in prices] if prices and prices[0] else prices
            fig.add_trace(go.Scatter(y=norm, mode="lines", name=coin.upper(), line=dict(width=2.5)))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,19,0.65)", font=dict(color="#ECFDF5"), height=300, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Quantitative Asset Metrics")
        st.dataframe(pd.DataFrame(res["metrics_rows"]), use_container_width=True, hide_index=True)

    with right:
        st.subheader("Strategist Regime Brief")
        st.info(res["synthesis"]["text"])
        alloc_df = pd.DataFrame(res["allocations"])
        fig_pie = px.pie(alloc_df, names="bucket", values="weight_pct", hole=0.52, title="Inverse-Volatility Risk-Parity Allocation (Sim)")
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECFDF5"), height=280, margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

with t2:
    st.subheader("Sub-Agent Quantitative Pipeline Trace")
    for m in res["messages"]:
        st.markdown(
            f'<div class="quant-bus"><div class="mono" style="font-size:0.78rem; color:#10B981;">[{m["phase"]}] {m["sender"]} → {m["recipient"]} (conf={m["confidence"]})</div><div style="margin-top:0.2rem;">{m["content"]}</div></div>',
            unsafe_allow_html=True,
        )

with t3:
    st.subheader("PEAS Specification")
    st.table(
        pd.DataFrame(
            [
                {"Component": "P — Performance Measure", "Description": "Drawdown containment via volatility-parity sizing, accurate regime detection, zero financial-advice overreach."},
                {"Component": "E — Environment", "Description": "Frankfurter ECB FX feed, CoinGecko market series, HN Algolia headlines, Streamlit & GitHub Actions."},
                {"Component": "A — Actuators", "Description": "Normalized performance chart, risk-parity allocation emitter, regime history logger."},
                {"Component": "S — Sensors", "Description": "Live FX rates, 30D daily close series, macro headlines, state/regime_memory.json."},
            ]
        )
    )
    if res["memory"].get("regime_history"):
        st.dataframe(pd.DataFrame(res["memory"]["regime_history"]), use_container_width=True, hide_index=True)
