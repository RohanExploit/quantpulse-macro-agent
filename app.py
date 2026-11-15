"""QuantPulse — Institutional Quant Terminal with Live n8n Workflow Animation."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from agents.orchestrator import QuantPulseStrategist
from agents.workflow_viz import render_n8n_workflow

st.set_page_config(
    page_title="QuantPulse | Autonomous Macro Strategist",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

ALL_COINS = ["bitcoin", "ethereum", "solana", "cardano", "chainlink", "avalanche-2", "ripple", "dogecoin"]
SAMPLES = {
    "Core Macro Majors (Default)": ["bitcoin", "ethereum", "solana"],
    "Smart-Contract L1 Basket": ["ethereum", "solana", "cardano", "avalanche-2"],
    "Full Multi-Asset Desk": ["bitcoin", "ethereum", "solana", "chainlink", "ripple"],
}

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
code, pre, .mono { font-family: 'JetBrains Mono', monospace !important; }
.stApp { background: radial-gradient(circle at 80% 10%, #0F1F2E 0%, #070B12 60%, #05080D 100%); }
@keyframes riseIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
.hero-qp {
    animation: riseIn .4s ease-out;
    background: linear-gradient(135deg, rgba(15,23,42,0.95), rgba(7,11,18,0.97));
    border: 1px solid rgba(16,185,129,0.34);
    border-radius: 14px;
    padding: 1.05rem 1.35rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 12px 28px rgba(0,0,0,0.42);
}
.kpi-qp {
    background: rgba(15,23,42,0.88);
    border: 1px solid rgba(148,163,184,0.2);
    border-radius: 12px;
    padding: 0.85rem 1rem;
    transition: transform .2s ease, border-color .2s ease;
}
.kpi-qp:hover { transform: translateY(-2px); border-color: #10B981; }
.kpi-l { color:#94A3B8; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.06em; }
.kpi-v { color:#F8FAFC; font-size:1.38rem; font-weight:700; margin-top:0.15rem; }
.reg-badge { background:rgba(16,185,129,0.16); color:#34D399; border:1px solid #10B981; padding:4px 12px; border-radius:999px; font-weight:700; font-size:0.78rem; font-family:'JetBrains Mono',monospace; }
</style>
""",
    unsafe_allow_html=True,
)

if "qp_coins" not in st.session_state:
    st.session_state.qp_coins = SAMPLES["Core Macro Majors (Default)"]


def _apply_sample() -> None:
    st.session_state.qp_coins = SAMPLES[st.session_state.qp_sample]
    st.session_state.qp_force = True


with st.sidebar:
    st.markdown("### Sample Portfolios")
    st.selectbox("Load Macro Basket Preset", list(SAMPLES.keys()), key="qp_sample", on_change=_apply_sample)
    st.markdown("### Asset Universe")
    selected_coins = st.multiselect("Tracked CoinGecko Assets", ALL_COINS, key="qp_coins")

    with st.expander("AI Brain Keys (Optional)"):
        gemini_key = st.text_input("Gemini API Key Override", type="password", placeholder="Auto via Secrets / Env")
        groq_key = st.text_input("Groq API Key Override", type="password", placeholder="Auto-fallback")

    run_btn = st.button("Execute Quant Regime Cycle", type="primary", width="stretch")
    st.caption("Vishal Chavan · BTCOC701 · Simulation Only")

if "qp_result" not in st.session_state or run_btn or st.session_state.pop("qp_force", False):
    with st.spinner("Running 4 quant sub-agents across Frankfurter ECB, CoinGecko & HN..."):
        st.session_state.qp_result = QuantPulseStrategist().run_analysis(
            coins=selected_coins or ["bitcoin", "ethereum"],
            gemini_key=gemini_key,
            groq_key=groq_key,
        )

res = st.session_state.qp_result
usd_inr = res["fx_basket"].get("rates", {}).get("INR", "N/A")
msgs = res["messages"]

st.markdown(
    f"""
<div class="hero-qp">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.6rem;">
    <div>
      <div style="font-size:1.6rem; font-weight:700; color:#F8FAFC;">QuantPulse — Macro Regime & Risk-Parity Terminal</div>
      <div class="mono" style="color:#94A3B8; font-size:0.82rem;">Frankfurter ECB FX · CoinGecko 30D Series · HN Algolia Divergence · Inverse-Vol Parity</div>
    </div>
    <div><span class="reg-badge">REGIME: {res['regime']}</span></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="kpi-qp"><div class="kpi-l">Market Regime</div><div class="kpi-v">{res["regime"]}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="kpi-qp"><div class="kpi-l">USD / INR Anchor</div><div class="kpi-v">{usd_inr}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="kpi-qp"><div class="kpi-l">Sentiment Index</div><div class="kpi-v">{res["sentiment_score"]:+.1f}</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="kpi-qp"><div class="kpi-l">AI Layer ({res["synthesis"]["latency_ms"]}ms)</div><div class="kpi-v" style="font-size:1.0rem;">{res["synthesis"]["model"]}</div></div>', unsafe_allow_html=True)

st.markdown("")
wf_nodes = [
    {"title": "QuantStrategist", "role": "Orchestrator", "phase": "TRIGGER", "metric": f"{len(res['metrics_rows'])} assets", "payload": f"Initiated multi-asset cycle & loaded {len(res['memory'].get('regime_history', []))} prior regimes", "confidence": 0.98, "color": "#10B981", "icon": "🎯"},
    {"title": "MacroFXScout", "role": "Scout 1", "phase": "SENSE", "metric": f"INR {usd_inr}", "payload": msgs[1]["content"] if len(msgs) > 1 else "Fetched ECB FX + 30D curves", "confidence": msgs[1]["confidence"] if len(msgs) > 1 else 0.95, "color": "#38BDF8", "icon": "💱"},
    {"title": "SentimentCritic", "role": "Critic", "phase": "SENTIMENT", "metric": f"{res['sentiment_score']:+.1f} idx", "payload": msgs[3]["content"] if len(msgs) > 3 else res["divergence_note"], "confidence": msgs[3]["confidence"] if len(msgs) > 3 else 0.89, "color": "#F59E0B", "icon": "📰"},
    {"title": "QuantRegimeEngine", "role": "Quant", "phase": "REGIME", "metric": res["regime"], "payload": msgs[2]["content"] if len(msgs) > 2 else "Computed Vol, RSI-14, MDD", "confidence": msgs[2]["confidence"] if len(msgs) > 2 else 0.94, "color": "#A78BFA", "icon": "📐"},
    {"title": "RiskParityAgent", "role": "Utility", "phase": "ALLOCATE", "metric": f"{len(res['allocations'])} buckets", "payload": msgs[4]["content"] if len(msgs) > 4 else "Computed inverse-volatility weights", "confidence": msgs[4]["confidence"] if len(msgs) > 4 else 0.94, "color": "#34D399", "icon": "⚖️"},
    {"title": "RegimeMemory + UI", "role": "Persister", "phase": "SYNC", "metric": res["synthesis"]["provider"].split()[0], "payload": f"Persisted {len(res['memory'].get('seen_headline_ids', []))} headlines ({res['memory'].get('total_runs', 1)} runs)", "confidence": 0.97, "color": "#10B981", "icon": "💾"},
]
render_n8n_workflow(
    wf_nodes,
    theme={"mode": "dark", "bg": "#070B12", "card_bg": "#0F172A", "border": "rgba(16,185,129,0.3)", "accent": "#10B981", "text": "#F8FAFC", "muted": "#94A3B8"},
    engine_label=f"QuantPulse DAG · {res['synthesis']['provider']}",
)

t1, t2, t3 = st.tabs(["Trajectory, Parity & FX", "Quant Matrix & Headlines", "Agent Bus & Memory"])

with t1:
    g1, g2 = st.columns([1.45, 1])
    with g1:
        norm_rows = []
        for coin, series in res["series_map"].items():
            base = series[0] if series and series[0] else 1.0
            for idx, val in enumerate(series):
                norm_rows.append({"Day": idx + 1, "Asset": coin.upper(), "Indexed (D1=100)": round((val / base) * 100.0, 2)})
        if norm_rows:
            fig_curve = px.line(pd.DataFrame(norm_rows), x="Day", y="Indexed (D1=100)", color="Asset", title="Normalized 30-Day Performance Curve (Day 1 = 100)", height=295)
            fig_curve.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.5)", font=dict(color="#E2E8F0"), margin=dict(l=10, r=10, t=38, b=10))
            st.plotly_chart(fig_curve, width="stretch")

    alloc_df = pd.DataFrame(res["allocations"])
    with g2:
        if not alloc_df.empty:
            fig_pie = px.pie(alloc_df, names="bucket", values="weight_pct", hole=0.52, title="Inverse-Volatility Risk-Parity Mix", height=295)
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E2E8F0"), margin=dict(l=10, r=10, t=38, b=10))
            st.plotly_chart(fig_pie, width="stretch")

    b1, b2 = st.columns([1.2, 1])
    m_df = pd.DataFrame(res["metrics_rows"])
    with b1:
        if not m_df.empty:
            fig_rr = px.scatter(
                m_df,
                x="ann_vol_pct",
                y="return_30d_pct",
                text="asset",
                color="rsi_14",
                color_continuous_scale="Tealgrn",
                title="Volatility vs 30-Day Return Frontier (Color = RSI-14)",
                height=260,
            )
            fig_rr.update_traces(textposition="top center", marker=dict(size=14, line=dict(width=1, color="#F8FAFC")))
            fig_rr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.5)", font=dict(color="#E2E8F0"), margin=dict(l=10, r=10, t=38, b=10))
            st.plotly_chart(fig_rr, width="stretch")

    with b2:
        rates = res["fx_basket"].get("rates", {})
        if rates:
            fx_df = pd.DataFrame([{"Currency": k, "Rate per 1 USD": float(v)} for k, v in rates.items()])
            fig_fx = px.bar(fx_df, x="Currency", y="Rate per 1 USD", text="Rate per 1 USD", title=f"ECB FX Anchor ({res['fx_basket'].get('source', '')})", height=260, color="Currency")
            fig_fx.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.5)", font=dict(color="#E2E8F0"), margin=dict(l=10, r=10, t=38, b=10), showlegend=False)
            st.plotly_chart(fig_fx, width="stretch")

    with st.expander(f"AI Macro Strategy Brief ({res['synthesis']['provider']} · {res['synthesis']['model']})", expanded=False):
        st.write(res["synthesis"]["text"])
        st.caption(f"Divergence Signal: {res['divergence_note']}")

with t2:
    if not m_df.empty:
        st.markdown("#### Multi-Asset Quantitative Scorecard")
        st.dataframe(
            m_df,
            width="stretch",
            hide_index=True,
            column_config={
                "spot_usd": st.column_config.NumberColumn("Spot USD", format="$%.2f"),
                "return_30d_pct": st.column_config.NumberColumn("30D Return", format="%.2f%%"),
                "ann_vol_pct": st.column_config.ProgressColumn("Ann. Vol %", min_value=0, max_value=150, format="%.1f%%"),
                "rsi_14": st.column_config.ProgressColumn("RSI-14", min_value=0, max_value=100, format="%.1f"),
                "max_drawdown_pct": st.column_config.NumberColumn("Max Drawdown", format="%.2f%%"),
            },
        )
    c_x, c_y = st.columns([1, 1.3])
    with c_x:
        if not alloc_df.empty:
            st.markdown("#### Risk-Parity Allocation Rationale")
            st.dataframe(alloc_df, width="stretch", hide_index=True, column_config={"weight_pct": st.column_config.ProgressColumn("Weight %", min_value=0, max_value=100, format="%.1f%%")})
    with c_y:
        st.markdown("#### HN Algolia Macro Signal Feed")
        hl_df = pd.DataFrame(res["headlines"])
        if not hl_df.empty:
            st.dataframe(hl_df[["title", "points", "url"]], width="stretch", hide_index=True, column_config={"url": st.column_config.LinkColumn("Source")})

with t3:
    msg_df = pd.DataFrame(msgs)
    if not msg_df.empty:
        fig_m = px.bar(msg_df, x="sender", y="confidence", color="phase", title="Sub-Agent Execution Confidence", height=240)
        fig_m.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.5)", font=dict(color="#E2E8F0"), margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig_m, width="stretch")
        st.dataframe(msg_df[["phase", "sender", "recipient", "confidence", "content"]], width="stretch", hide_index=True)

    hist = res["memory"].get("regime_history", [])
    if hist:
        st.plotly_chart(px.line(pd.DataFrame(hist), x="timestamp_utc", y="annualized_vol_pct", markers=True, title="Persistent Regime Volatility History", height=220).update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.5)", font=dict(color="#E2E8F0")), width="stretch")

    st.table(
        pd.DataFrame(
            [
                {"PEAS": "Performance", "Spec": "Inverse-vol drawdown defense, divergence sensitivity, regime Sharpe"},
                {"PEAS": "Environment", "Spec": "Frankfurter ECB FX, CoinGecko 30D REST, HN Algolia Macro Feed"},
                {"PEAS": "Actuators", "Spec": "Quant Terminal UI, Risk-Parity Mix, state/regime_memory.json"},
                {"PEAS": "Sensors", "Spec": "Daily closes, FX crosses, headline keywords & point weights"},
            ]
        )
    )
