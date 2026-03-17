import io
import os
from typing import List, Dict

import streamlit as st
import pandas as pd
import requests

from app import get_odds, find_arbitrage, compute_stakes
from data_store import save_snapshot, load_master, save_detailed_odds


st.set_page_config(page_title="Sports Bet Arbitrage", layout="wide")

# Custom CSS styling
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #0e1117, #1a1d24);
}

h1, h2, h3 {
    font-family: 'Segoe UI', sans-serif;
    letter-spacing: 1px;
    color: #00ffcc;
}

.block-container {
    padding-top: 2rem;
}

.game-card {
    background-color: #1a1d24;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 20px;
    box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.5);
    border-left: 4px solid #00ffcc;
}

.odds-display {
    text-align: center;
    padding: 15px;
}

.odds-value {
    color: #00ffcc;
    font-size: 2.5em;
    font-weight: bold;
}

.team-name {
    color: #ffffff;
    font-size: 1.2em;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# Utility Functions
def american_odds(decimal_odds):
    """Convert decimal odds to American format."""
    if decimal_odds >= 2:
        return f"+{int((decimal_odds - 1) * 100)}"
    else:
        return f"{int(-100 / (decimal_odds - 1))}"

def display_game_card(teams: List[str], best_odds: Dict[str, float], arb_value: float, profit: float, profit_pct: float):
    """Display a game as a professional card."""
    away, home = (teams[0], teams[1]) if len(teams) >= 2 else (teams[0] if teams else "Team A", "Team B")
    
    st.markdown(f"""
    <div class="game-card">
        <h2 style="text-align: center; margin-bottom: 20px;">🎮 {away} @ {home}</h2>
    """, unsafe_allow_html=True)
    
    cols = st.columns([1, 1, 1])
    
    # Team 1
    with cols[0]:
        odds_a = best_odds.get(away, 0)
        st.markdown(f"""
        <div class="odds-display">
            <div class="team-name">{away}</div>
            <div class="odds-value">{american_odds(odds_a) if odds_a > 0 else "N/A"}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Metrics
    with cols[1]:
        st.markdown(f"""
        <div class="odds-display">
            <div style="color: #888; font-size: 0.9em; margin-bottom: 10px;">ARB VALUE</div>
            <div class="odds-value">{arb_value:.4f}</div>
            <div style="color: #00ff00; font-size: 0.85em; margin-top: 10px;">💰 ${profit:.2f} ({profit_pct:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Team 2
    with cols[2]:
        odds_b = best_odds.get(home, 0)
        st.markdown(f"""
        <div class="odds-display">
            <div class="team-name">{home}</div>
            <div class="odds-value">{american_odds(odds_b) if odds_b > 0 else "N/A"}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

st.title("💰 Live Betting Dashboard")
st.markdown("**Real-time arbitrage detection — guaranteed wins across bookmakers**")

# Team logo mapping (expand as needed)
TEAM_LOGOS = {
    "Charlotte Hornets": "https://upload.wikimedia.org/wikipedia/en/c/c4/Charlotte_Hornets_logo.png",
    "Miami Heat": "https://upload.wikimedia.org/wikipedia/en/f/fb/Miami_Heat_logo.png",
    "Boston Celtics": "https://upload.wikimedia.org/wikipedia/en/1/10/Boston_Celtics.svg",
    "Los Angeles Lakers": "https://upload.wikimedia.org/wikipedia/en/3/3c/Los_Angeles_Lakers.svg",
}

# Fetch available sports from API
@st.cache_data(ttl=3600)
def get_available_sports(api_key):
    try:
        resp = requests.get(f"https://api.the-odds-api.com/v4/sports/?apiKey={api_key}")
        if resp.status_code == 200:
            sports = resp.json()
            return {s['title']: s['key'] for s in sports}
        return {"NBA": "basketball_nba", "NFL": "americanfootball_nfl", "MLB": "baseball_mlb"}
    except:
        return {"NBA": "basketball_nba", "NFL": "americanfootball_nfl", "MLB": "baseball_mlb"}

with st.sidebar:
    st.subheader("⚙️ Settings")
    
    api_key = st.text_input("API Key", value=os.environ.get('ODDS_API_KEY', ''), type='password')
    
    if api_key:
        sports_map = get_available_sports(api_key)
        sport_name = st.selectbox("Sport", list(sports_map.keys()), index=0)
        sport = sports_map[sport_name]
    else:
        sport = st.text_input("Sport code (e.g., basketball_nba)", value="basketball_nba")
    
    region = st.selectbox("Region", ["us", "eu", "uk", "au"], index=0)
    
    markets = st.multiselect(
        "Bet Types",
        ["h2h", "spreads", "totals"],
        default=["h2h"]
    )
    
    if not markets:
        markets = ["h2h"]
    
    markets_str = ",".join(markets)
    
    stake = st.number_input("Total stake (for calculations)", value=100.0, min_value=1.0)
    refresh_seconds = st.slider("Auto-refresh (seconds)", min_value=10, max_value=600, value=60, step=10)
    auto_refresh = st.checkbox("Enable auto-refresh", value=True)
    arb_threshold = st.number_input("Max Arb Value (<=)", value=0.99, step=0.001, format="%.3f")
    team_filter = st.text_input("Team filter (optional)", value="")
    
    st.divider()
    submit = st.button("🔍 Fetch Odds", use_container_width=True)

# cached fetch using TTL so auto-refresh works without rerunning entire script
@st.cache_data(ttl=0)
def cached_get_odds_no_cache(api_key, sport, region, markets_str):
    return get_odds(api_key, sport, region, markets_str)

def cached_get_odds(api_key, sport, region, markets_str, ttl):
    if ttl <= 0:
        return cached_get_odds_no_cache(api_key, sport, region, markets_str)

    @st.cache_data(ttl=ttl)
    def _f(k, s, r, m):
        return get_odds(k, s, r, m)

    return _f(api_key, sport, region, markets_str)

if not api_key:
    st.warning("Provide an API key in the sidebar or set the ODDS_API_KEY environment variable.")

if submit and api_key:
    with st.spinner("Fetching odds..."):
        if auto_refresh:
            data = cached_get_odds(api_key, sport, region, markets_str, refresh_seconds)
        else:
            data = cached_get_odds_no_cache(api_key, sport, region, markets_str)

    if not data:
        st.info("No data returned from the API.")
    else:
        # Save detailed bookmaker-level odds for line movement tracking
        save_detailed_odds(data)
        
        arbs = find_arbitrage(data)

        # build rows
        rows: List[Dict] = []
        for arb in arbs:
            teams = arb["teams"]
            best = arb["odds"]
            arb_value = arb["arb_value"]
            if arb_value > arb_threshold:
                continue
            team_names = list(best.keys())
            odds_vals = [best[team_names[0]], best[team_names[1]]]
            stake_a, stake_b, profit, profit_pct = compute_stakes(odds_vals[0], odds_vals[1], total=stake)

            row = {
                "Match": " vs ".join(teams),
                "Team A": team_names[0],
                "Odds A": odds_vals[0],
                "Team B": team_names[1],
                "Odds B": odds_vals[1],
                "Arb": round(arb_value, 4),
                "Stake A": stake_a,
                "Stake B": stake_b,
                "Profit": profit,
                "Profit %": profit_pct,
            }

            if team_filter:
                if team_filter.lower() not in row["Match"].lower():
                    continue

            rows.append(row)

        df = pd.DataFrame(rows)

        # UI: display and allow saving
        st.subheader("💰 Arbitrage Opportunities")
        if df.empty:
            st.warning("❌ No arbitrage found right now. Try different settings.")
        else:
            st.success(f"✅ Found {len(df)} arbitrage opportunities!")
            
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Opps", len(df))
            with col2:
                st.metric("Avg Profit", f"${df['Profit'].mean():.2f}")
            with col3:
                st.metric("Max Profit", f"${df['Profit'].max():.2f}")
            with col4:
                st.metric("Avg ROI", f"{df['Profit %'].mean():.2f}%")
            
            st.divider()
            
            # Display each opportunity as a card
            st.subheader("🎮 Game Cards")
            for idx, row in df.iterrows():
                teams = row["Match"].split(" vs ")
                best_odds_dict = {
                    row["Team A"]: row["Odds A"],
                    row["Team B"]: row["Odds B"],
                }
                display_game_card(teams, best_odds_dict, row["Arb"], row["Profit"], row["Profit %"])
            
            st.divider()
            
            # Detailed table view
            with st.expander("📊 Detailed Table View"):
                st.dataframe(df, use_container_width=True)

            # CSV download & snapshot buttons
            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False)
            csv_bytes = csv_buf.getvalue().encode('utf-8')

            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                st.download_button("📥 Download CSV", data=csv_bytes, file_name="arbitrage.csv", mime="text/csv", use_container_width=True)
            with col2:
                if st.button("💾 Save Snapshot", use_container_width=True):
                    try:
                        path = save_snapshot(df)
                        st.success(f"✅ Saved: {path}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            with col3:
                pass

        # Optional: show raw JSON & bookmaker details
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("📊 Raw API Response"):
                st.json(data[0] if data else {})
        
        with col2:
            if data:
                with st.expander("📍 Bookmaker Details"):
                    for game in data[:3]:  # Show first 3 games
                        for bm in game.get("bookmakers", [])[:2]:  # Show first 2 bookmakers
                            st.write(f"**{bm.get('title')}**")
                            for market in bm.get("markets", []):
                                st.caption(f"{market.get('key')}: {[o.get('price') for o in market.get('outcomes', [])]}")

        # Analytics from master CSV
        master = load_master()
        if not master.empty:
            st.subheader("📈 Analytics — Historical Trends")
            try:
                master["fetched_at"] = pd.to_datetime(master["fetched_at"])
                summary = master.groupby(master["fetched_at"]).agg({
                    "Match": "count",
                    "Profit": "mean",
                }).rename(columns={"Match": "opps_count", "Profit": "avg_profit"}).sort_index()

                st.line_chart(summary[["opps_count"]])
                st.line_chart(summary[["avg_profit"]])
            except Exception:
                st.info("Not enough historical data for analytics yet.")

st.markdown("---")
st.markdown("Built on the existing CLI functions in `app.py`. Use the sidebar to change settings and fetch live odds.")
