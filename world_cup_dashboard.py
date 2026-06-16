import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="World Cup 2026 Winner Vs Goldern Boot Winner Market Analytics",
    page_icon="⚽",
    layout="wide"
)

# ──────────────────────────────────────────
# DATA FETCHING
# ──────────────────────────────────────────

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_event_data(slug):
    """Fetch event data from Polymarket Gamma API"""
    url = f"https://gamma-api.polymarket.com/events?slug={slug}"
    resp = requests.get(url, timeout=15)
    if resp.status_code == 200 and len(resp.json()) > 0:
        return resp.json()[0]
    return None

@st.cache_data(ttl=300)
def get_markets_for_event(event_id):
    """Fetch all markets within an event"""
    all_markets = []
    cursor = None
    while True:
        url = f"https://gamma-api.polymarket.com/markets?event_id={event_id}&limit=50"
        if cursor:
            url += f"&cursor={cursor}"
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            break
        data = resp.json()
        all_markets.extend(data)
        # Check for cursor in response headers or body
        if isinstance(data, list) and len(data) < 50:
            break
        cursor = resp.headers.get("next-cursor")
        if not cursor:
            break
    return all_markets

# ──────────────────────────────────────────
# FETCH BOTH EVENTS
# ──────────────────────────────────────────

st.title("⚽ 2026 World Cup · Prediction Market Analytics")
st.markdown(f"*Data sourced from Polymarket Gamma API · Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*")

# World Cup Winner
wc_event = get_event_data("world-cup-winner")
# Golden Boot Winner  
gb_event = get_event_data("world-cup-golden-boot-winner")

if not wc_event or not gb_event:
    st.error("Could not fetch data from Polymarket API. Please try again later.")
    st.stop()

# ──────────────────────────────────────────
# HEADER METRICS
# ──────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🏆 World Cup Winner Volume", 
              f"${wc_event['volume']:,.0f}",
              f"${wc_event.get('volume24hr', 0):,.0f} today")

with col2:
    st.metric("👟 Golden Boot Winner Volume",
              f"${gb_event['volume']:,.0f}",
              f"${gb_event.get('volume24hr', 0):,.0f} today")

volume_ratio = wc_event['volume'] / gb_event['volume']

with col3:
    st.metric("📊 Volume Ratio", f"{volume_ratio:.0f}x",
              "Winner vs Golden Boot")

with col4:
    wc_liquidity = wc_event.get('liquidity', 0)
    gb_liquidity = gb_event.get('liquidity', 0)
    st.metric("💧 Total Liquidity",
              f"${(wc_liquidity + gb_liquidity):,.0f}",
              f"${wc_liquidity:,.0f} (WC) · ${gb_liquidity:,.0f} (GB)")

# ──────────────────────────────────────────
# MAIN COMPARISON TABLE
# ──────────────────────────────────────────

st.subheader("📊 Side-by-Side Comparison")

data = [
    {
        "Metric": "Total Volume (USD)",
        "🏆 World Cup Winner": f"${wc_event['volume']:,.0f}",
        "👟 Golden Boot Winner": f"${gb_event['volume']:,.0f}",
        "Difference": f"{volume_ratio:.0f}x"
    },
    {
        "Metric": "24h Volume",
        "🏆 World Cup Winner": f"${wc_event.get('volume24hr', 0):,.0f}",
        "👟 Golden Boot Winner": f"${gb_event.get('volume24hr', 0):,.0f}",
        "Difference": f"{wc_event.get('volume24hr', 0) / max(gb_event.get('volume24hr', 1), 1):.0f}x"
    },
    {
        "Metric": "Liquidity",
        "🏆 World Cup Winner": f"${wc_event.get('liquidity', 0):,.0f}",
        "👟 Golden Boot Winner": f"${gb_event.get('liquidity', 0):,.0f}",
        "Difference": f"{wc_event.get('liquidity', 0) / max(gb_event.get('liquidity', 1), 1):.0f}x"
    },
    {
        "Metric": "Open Interest",
        "🏆 World Cup Winner": f"${wc_event.get('openInterest', 0):,.0f}",
        "👟 Golden Boot Winner": f"${gb_event.get('openInterest', 0):,.0f}",
        "Difference": f"{wc_event.get('openInterest', 0) / max(gb_event.get('openInterest', 1), 1):.0f}x"
    },
    {
        "Metric": "Markets (Outcomes)",
        "🏆 World Cup Winner": f"{len(wc_event.get('markets', []))}",
        "👟 Golden Boot Winner": f"{len(gb_event.get('markets', []))}",
        "Difference": ""
    },
    {
        "Metric": "Start Date",
        "🏆 World Cup Winner": wc_event['startDate'][:10],
        "👟 Golden Boot Winner": gb_event['startDate'][:10],
        "Difference": ""
    },
    {
        "Metric": "End Date",
        "🏆 World Cup Winner": wc_event['endDate'][:10],
        "👟 Golden Boot Winner": gb_event['endDate'][:10],
        "Difference": ""
    },
]

df_display = pd.DataFrame(data)
st.table(df_display.set_index("Metric"))

# ──────────────────────────────────────────
# VISUALIZATION
# ──────────────────────────────────────────

st.subheader("📈 Volume Comparison")

chart_data = pd.DataFrame({
    "Market": ["World Cup Winner", "Golden Boot Winner"],
    "Volume (USD)": [wc_event['volume'], gb_event['volume']],
    "24h Volume": [wc_event.get('volume24hr', 0), gb_event.get('volume24hr', 0)],
    "Liquidity": [wc_event.get('liquidity', 0), gb_event.get('liquidity', 0)]
})

col_a, col_b = st.columns(2)

with col_a:
    fig1 = px.bar(chart_data, x="Market", y="Volume (USD)",
                  title="Total Volume (USD)",
                  text_auto=".2s",
                  color="Market",
                  color_discrete_map={
                      "World Cup Winner": "#1a73e8",
                      "Golden Boot Winner": "#34a853"
                  })
    fig1.update_layout(showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    fig2 = px.bar(chart_data, x="Market", y="Liquidity",
                  title="Liquidity (USD)",
                  text_auto=".2s",
                  color="Market",
                  color_discrete_map={
                      "World Cup Winner": "#1a73e8",
                      "Golden Boot Winner": "#34a853"
                  })
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

# ──────────────────────────────────────────
# TOP OUTCOMES (World Cup Winner)
# ──────────────────────────────────────────

st.subheader("🏆 World Cup Winner - Top Contenders")

wc_markets = wc_event.get('markets', [])
# Sort by volume to get the most traded outcomes
wc_markets_sorted = sorted(wc_markets, key=lambda m: float(m.get('volumeNum', 0) or 0), reverse=True)

# Get top 10 by volume
top_10 = []
for m in wc_markets_sorted[:10]:
    outcome_name = m.get('groupItemTitle', '') or m.get('title', '').replace("Will ", "").replace(" win the 2026 FIFA World Cup?", "")
    top_10.append({
        "Team": outcome_name,
        "Volume": float(m.get('volumeNum', 0) or 0),
        "Price": float(m.get('lastTradePrice', 0) or 0),
        "Probability": f"{float(m.get('lastTradePrice', 0) or 0) * 100:.1f}%",
        "Liquidity": float(m.get('liquidityNum', 0) or 0)
    })

if top_10:
    df_top = pd.DataFrame(top_10)
    col_c, col_d = st.columns([2, 1])
    
    with col_c:
        fig3 = px.bar(df_top.head(8), x="Team", y="Volume",
                      title="Top 8 Teams by Trading Volume",
                      text_auto=".2s", color="Volume",
                      color_continuous_scale="blues")
        fig3.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col_d:
        st.dataframe(df_top[["Team", "Volume", "Probability", "Liquidity"]].head(8),
                    column_config={
                        "Volume": st.column_config.NumberColumn(format="$%.0f"),
                        "Liquidity": st.column_config.NumberColumn(format="$%.0f")
                    },
                    hide_index=True,
                    use_container_width=True)

# ──────────────────────────────────────────
# GOLDEN BOOT TOP OUTCOMES
# ──────────────────────────────────────────

st.subheader("👟 Golden Boot Winner - Top Contenders")

gb_markets = gb_event.get('markets', [])
gb_markets_sorted = sorted(gb_markets, key=lambda m: float(m.get('volumeNum', 0) or 0), reverse=True)

top_gb = []
for m in gb_markets_sorted[:10]:
    outcome_name = m.get('groupItemTitle', '') or m.get('title', '').replace("World Cup Golden Boot Winner - ", "")
    top_gb.append({
        "Player": outcome_name,
        "Volume": float(m.get('volumeNum', 0) or 0),
        "Price": float(m.get('lastTradePrice', 0) or 0),
        "Probability": f"{float(m.get('lastTradePrice', 0) or 0) * 100:.1f}%",
        "Liquidity": float(m.get('liquidityNum', 0) or 0)
    })

if top_gb:
    col_e, col_f = st.columns([2, 1])
    
    with col_e:
        fig4 = px.bar(pd.DataFrame(top_gb).head(8), x="Player", y="Volume",
                      title="Top 8 Players by Trading Volume",
                      text_auto=".2s", color="Volume",
                      color_continuous_scale="greens")
        fig4.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig4, use_container_width=True)
    
    with col_f:
        st.dataframe(pd.DataFrame(top_gb)[["Player", "Volume", "Probability", "Liquidity"]].head(8),
                    column_config={
                        "Volume": st.column_config.NumberColumn(format="$%.0f"),
                        "Liquidity": st.column_config.NumberColumn(format="$%.0f")
                    },
                    hide_index=True,
                    use_container_width=True)

# ──────────────────────────────────────────
# KEY INSIGHT
# ──────────────────────────────────────────

st.divider()
st.subheader("💡 Key Insight")

st.info(f"""
**Volume Multiples (🏆 Winner ÷ 👟 Golden Boot):**

| Metric | Multiplier |
|---|---|
| Total Volume | **{volume_ratio:.0f}x** |
| 24h Volume | **{wc_event.get('volume24hr', 0) / max(gb_event.get('volume24hr', 1), 1):.0f}x** |
| Liquidity | **{wc_event.get('liquidity', 0) / max(gb_event.get('liquidity', 1), 1):.0f}x** |

**Why such a massive gap between two markets from the same tournament?**

1. 🧠 **Lower cognitive load** — Picking a tournament winner is intuitive. Predicting a top scorer requires tracking individual form, group stage matchups, penalty takers, and tournament bracket depth.

2. ✅ **Higher resolution confidence** — The World Cup winner is unambiguous (who lifts the trophy). The Golden Boot has tiebreaker complexity (what if two players have the same goals? What about penalty kicks vs open play?).

3. 📊 **Information accessibility** — Team stats, form, and odds are everywhere. Individual player goal-scoring projections require much more niche analysis.

**The takeaway:** Liquidity isn't just a function of the event's importance. It's driven by how easy a market is to **understand**, **research**, and **feel confident trading**.
""")

# ──────────────────────────────────────────
# RAW API DATA (expandable)
# ──────────────────────────────────────────

with st.expander("📋 Raw API Data (for verification)"):
    col_raw1, col_raw2 = st.columns(2)
    with col_raw1:
        st.json(wc_event)
    with col_raw2:
        st.json(gb_event)

st.caption(f"Built with Polymarket Gamma API · No API key required · Data refreshes every 5 minutes")