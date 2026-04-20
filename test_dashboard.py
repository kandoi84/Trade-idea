import streamlit as st
import pandas as pd
import pyodbc
import plotly.graph_objects as go
from pyvis.network import Network
import streamlit.components.v1 as components
from datetime import datetime

# --- CONFIGURATION ---
DB_CONFIG = {
    "server": r"KAPIL-LAPTOP\SQLEXPRESS",
    "database": "NiftyDataDB"
}

# --- STYLING (The "Sleek" Magic) ---
st.set_page_config(page_title="Nifty AI Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    div[data-testid="stMetricValue"] { color: #00d1ff; font-size: 24px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #161b22; border-radius: 5px 5px 0 0; padding: 10px 20px; color: #8b949e; 
    }
    .stTabs [aria-selected="true"] { background-color: #21262d !important; color: white !important; border-bottom: 2px solid #00d1ff !important; }
    </style>
    """, unsafe_allow_items=True)

# --- ENGINE ---
@st.cache_data(ttl=60)
def fetch_data():
    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};Trusted_Connection=yes;"
    try:
        with pyodbc.connect(conn_str) as conn:
            # Fetch TOP 500 to ensure speed
            df = pd.read_sql("SELECT TOP 500 * FROM MarketData ORDER BY Datetime DESC", conn)
            df['Datetime'] = pd.to_datetime(df['Datetime'])
            return df
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()

def generate_ai_insight(row):
    """The AI Brain: Analyzes technicals for instant feedback"""
    rsi = row['RSI']
    ltp = row['LTP']
    ema21 = row['EMA_21']
    
    if rsi > 70: insight = "⚠️ OVERBOUGHT: Price is stretched. Watch for a pullback."
    elif rsi < 30: insight = "🚀 OVERSOLD: Potential bounce incoming."
    elif ltp > ema21: insight = "📈 TREND BULLISH: Trading above 21-EMA. Momentum is up."
    else: insight = "📉 TREND BEARISH: Under pressure. Resistance at 21-EMA."
    return insight

def get_obsidian_graph(row):
    """Creates the Obsidian-style interaction map"""
    net = Network(height="450px", width="100%", bgcolor="#0E1117", font_color="white")
    sym = row['Symbol']
    
    # Nodes
    net.add_node(sym, label=sym, color='#00d1ff', size=35, shape="diamond", shadow=True)
    nodes = {
        f"LTP: {row['LTP']}": "#90ee90",
        f"RSI: {row['RSI']:.1f}": "#ff4b4b" if row['RSI'] > 70 else "#90ee90",
        f"SIGNAL: {row['Signal']}": "#ffffff",
        f"EMA9: {row['EMA_9']:.0f}": "#ffa500"
    }
    
    for label, color in nodes.items():
        net.add_node(label, label=label, color=color, size=15, shadow=True)
        net.add_edge(sym, label, color="#444", width=2)
    
    net.toggle_physics(True)
    return net.generate_html()

# --- THE DASHBOARD ---
@st.fragment(run_every="1m")
def main():
    # Top Bar
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("🛰️ Nifty Intelligence Terminal")
    with c2:
        if st.button("🔄 Force Refresh Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    df = fetch_data()
    if df.empty: return

    latest = df.iloc[0]
    prev = df.iloc[1] if len(df) > 1 else latest

    # AI Insight Section
    st.info(f"**AI ANALYST:** {generate_ai_insight(latest)}")

    # KPI Strip
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("LTP", f"₹{latest['LTP']}", delta=f"{latest['LTP'] - prev['LTP']:.2f}")
    k2.metric("RSI (14)", f"{latest['RSI']:.2f}", delta_color="off")
    k3.metric("Volume", f"{latest['Volume']:,}")
    k4.metric("Signal", latest['Signal'])

    # Tabs for Content
    t_chart, t_graph, t_data = st.tabs(["📊 Technical Chart", "🕸️ Obsidian Map", "📋 Deep Data"])

    with t_chart:
        # Candle Chart with Modern Layout
        fig = go.Figure(data=[go.Candlestick(
            x=df['Datetime'], open=df['Open'], high=df['High'], low=df['Low'], close=df['LTP'],
            name="Nifty"
        )])
        fig.add_trace(go.Scatter(x=df['Datetime'], y=df['EMA_9'], name="EMA 9", line=dict(color='#00d1ff', width=1)))
        fig.add_trace(go.Scatter(x=df['Datetime'], y=df['EMA_21'], name="EMA 21", line=dict(color='#ff9900', width=1)))
        fig.update_layout(
            template="plotly_dark", height=550, 
            xaxis_rangeslider_visible=False,
            margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with t_graph:
        st.write("### Entity Relationship (Obsidian View)")
        graph_html = get_obsidian_graph(latest)
        components.html(graph_html, height=500)

    with t_data:
        st.dataframe(df, use_container_width=True, height=500)

    # Footer
    st.caption(f"Last heartbeat: {datetime.now().strftime('%H:%M:%S')} | Auto-refresh: 60s")

if __name__ == "__main__":
    main()