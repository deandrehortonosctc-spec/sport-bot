import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List
import streamlit as st
import pandas as pd
import requests

from app import get_odds, find_arbitrage, compute_stakes
from data_store import save_snapshot, save_detailed_odds

st.set_page_config(page_title="Chegy Bets - Smart Arbitrage Betting", layout="wide")

# ============================================================================
# PROFESSIONAL THEME & STYLING
# ============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&family=Space+Mono:wght@400;700&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

body {
    background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 50%, #16213e 100%);
    overflow-x: hidden;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Space Mono', monospace;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.main {
    background: transparent;
}

.block-container {
    padding-top: 0;
    padding-bottom: 3rem;
}

/* Hero Section */
.hero-section {
    background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.1));
    border-left: 5px solid #6366f1;
    border-radius: 12px;
    padding: 40px;
    margin-bottom: 40px;
    box-shadow: 0 8px 32px rgba(99,102,241,0.15);
    position: relative;
    overflow: hidden;
}

.hero-section::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(139,92,246,0.1), transparent);
    pointer-events: none;
}

.hero-title {
    font-size: 3.5em;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 10px;
    font-weight: 900;
    letter-spacing: -1px;
}

.hero-subtitle {
    font-size: 1.2em;
    color: #a0a0b0;
    font-weight: 300;
    letter-spacing: 0.5px;
}

/* Game Card - Professional */
.game-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.4);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.game-card:hover {
    border-color: #6366f1;
    box-shadow: 0 20px 60px rgba(99,102,241,0.2);
    transform: translateY(-4px);
}

.game-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, #6366f1, transparent);
}

.team-section {
    text-align: center;
    padding: 20px;
}

.team-image {
    width: 100%;
    max-width: 120px;
    height: 120px;
    object-fit: contain;
    margin-bottom: 12px;
    filter: drop-shadow(0 4px 12px rgba(20,184,166,0.2));
    transition: all 0.3s ease;
}

.team-image:hover {
    transform: scale(1.05);
    filter: drop-shadow(0 8px 16px rgba(20,184,166,0.4));
}

.team-name {
    font-size: 1.1em;
    color: #e0e0e0;
    font-weight: 600;
    margin-bottom: 8px;
}

.odds-display {
    background: rgba(20,184,166,0.1);
    border: 2px solid #14b8a6;
    border-radius: 12px;
    padding: 16px;
    margin-top: 12px;
}

.odds-value {
    font-size: 2.2em;
    color: #14b8a6;
    font-family: 'Space Mono', monospace;
    font-weight: 700;
    letter-spacing: 1px;
}

.odds-label {
    font-size: 0.85em;
    color: #a0a0b0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

/* Bookmaker Grid */
.bookmaker-card {
    background: rgba(20,184,166,0.05);
    border: 1px solid rgba(20,184,166,0.2);
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    transition: all 0.2s ease;
}

.bookmaker-card:hover {
    background: rgba(20,184,166,0.1);
    border-color: #14b8a6;
}

.bookmaker-name {
    font-size: 0.9em;
    color: #a0a0b0;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
}

.bookmaker-odds {
    font-size: 1.5em;
    color: #14b8a6;
    font-family: 'Space Mono', monospace;
    font-weight: 700;
}

/* Metrics */
.metric-card {
    background: linear-gradient(135deg, rgba(20,184,166,0.1), rgba(139,92,246,0.1));
    border-left: 4px solid #14b8a6;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
}

.metric-value {
    font-size: 2em;
    color: #14b8a6;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
}

.metric-label {
    font-size: 0.85em;
    color: #a0a0b0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 8px;
}

/* Status Badges */
.badge-success {
    background: rgba(16,185,129,0.2);
    border: 1px solid #10b981;
    color: #10b981;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 0.9em;
    font-weight: 600;
    display: inline-block;
    margin-bottom: 20px;
}

.badge-empty {
    background: rgba(239,68,68,0.2);
    border: 1px solid #ef4444;
    color: #ef4444;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 0.9em;
    font-weight: 600;
    display: inline-block;
}

/* Divider */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(20,184,166,0.3), transparent);
    margin: 30px 0;
}

/* Geometric background elements */
.geo-element {
    position: fixed;
    pointer-events: none;
    opacity: 0.03;
    z-index: -1;
}

.geo-circle-1 {
    top: 5%;
    right: 5%;
    width: 300px;
    height: 300px;
    border: 2px solid #14b8a6;
    border-radius: 50%;
}

.geo-circle-2 {
    bottom: 10%;
    left: 5%;
    width: 400px;
    height: 400px;
    border: 2px solid #8b5cf6;
    border-radius: 50%;
}

.geo-triangle {
    top: 50%;
    right: 10%;
    width: 0;
    height: 0;
    border-left: 200px solid transparent;
    border-right: 200px solid transparent;
    border-bottom: 300px solid #14b8a6;
}
</style>

<!-- Geometric background elements -->
<div class="geo-element geo-circle-1"></div>
<div class="geo-element geo-circle-2"></div>
<div class="geo-triangle"></div>
""", unsafe_allow_html=True)

# ============================================================================
# USERS DATABASE (Local JSON)
# ============================================================================

USERS_FILE = "users.json"

def load_users() -> Dict:
    """Load users from JSON file."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users: Dict):
    """Save users to JSON file."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hash_password("chegy2024")

def login(username: str, password: str) -> bool:
    """Authenticate user."""
    if username == ADMIN_USERNAME:
        return hash_password(password) == ADMIN_PASSWORD_HASH
    users = load_users()
    if username in users:
        return users[username]["password_hash"] == hash_password(password)
    return False

def register_user(username: str, password: str, tier: str = "free"):
    """Register new user."""
    users = load_users()
    if username in users:
        return False
    users[username] = {
        "password_hash": hash_password(password),
        "tier": tier,
        "created_at": datetime.now().isoformat(),
    }
    save_users(users)
    return True

def get_user_tier(username: str) -> str:
    """Get user tier."""
    if username == ADMIN_USERNAME:
        return "admin"
    users = load_users()
    return users.get(username, {}).get("tier", "free")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def american_odds(decimal_odds):
    """Convert decimal odds to American format."""
    if decimal_odds >= 2:
        return f"+{int((decimal_odds - 1) * 100)}"
    else:
        return f"{int(-100 / (decimal_odds - 1))}"

@st.cache_data(ttl=3600)
def get_available_sports(api_key):
    """Fetch all available sports from API."""
    try:
        resp = requests.get(f"https://api.the-odds-api.com/v4/sports/?apiKey={api_key}")
        if resp.status_code == 200:
            sports = resp.json()
            return {s['title']: s['key'] for s in sports}
        return {"NFL": "americanfootball_nfl", "NBA": "basketball_nba", "MLB": "baseball_mlb", "NHL": "icehockey_nhl", "MLS": "soccer_usa_mls"}
    except:
        return {"NFL": "americanfootball_nfl", "NBA": "basketball_nba", "MLB": "baseball_mlb", "NHL": "icehockey_nhl", "MLS": "soccer_usa_mls"}

# Popular sportsbooks
SPORTSBOOKS = {
    "DraftKings": "draftkings",
    "FanDuel": "fanduel",
    "BetMGM": "betmgm",
    "Caesars": "caesars",
    "PointsBet": "pointsbet",
    "Barstool": "barstool",
}

# Team logos mapping
TEAM_LOGOS = {
    "Kansas City Chiefs": "https://a.espncdn.com/media/motion/2022/0328/dm_220328_nfl_chiefs_logo.png",
    "Buffalo Bills": "https://a.espncdn.com/media/motion/2022/0328/dm_220328_nfl_bills_logo.png",
    "Los Angeles Lakers": "https://a.espncdn.com/media/motion/2022/0328/dm_220328_nba_lakers_logo.png",
    "Boston Celtics": "https://a.espncdn.com/media/motion/2022/0328/dm_220328_nba_celtics_logo.png",
}

def display_professional_game_card(teams: List[str], best_odds: Dict, all_bookmaker_odds: Dict, arb_value: float, profit: float, profit_pct: float):
    """Display game as professional Pikkit-style card."""
    away, home = (teams[0], teams[1]) if len(teams) >= 2 else ("Team A", "Team B")
    
    st.markdown(f"""
    <div class="game-card">
        <div style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 20px; align-items: center;">
            <!-- Away Team -->
            <div class="team-section">
                <img src="{TEAM_LOGOS.get(away, 'https://via.placeholder.com/120')}" class="team-image" onerror="this.style.display='none'">
                <div class="team-name">{away}</div>
                <div class="odds-display">
                    <div class="odds-label">Best Odds</div>
                    <div class="odds-value">{american_odds(best_odds.get(away, 0))}</div>
                </div>
            </div>
            
            <!-- Match Info & Arbitrage -->
            <div style="text-align: center; padding: 20px; border-right: 1px solid rgba(20,184,166,0.2); border-left: 1px solid rgba(20,184,166,0.2);">
                <div style="color: #a0a0b0; font-size: 0.9em; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.5px;">vs</div>
                <div style="background: rgba(20,184,166,0.15); border-radius: 8px; padding: 12px; margin-bottom: 15px;">
                    <div style="color: #a0a0b0; font-size: 0.8em; text-transform: uppercase;">ARB VALUE</div>
                    <div style="color: #14b8a6; font-size: 1.8em; font-family: 'Space Mono', monospace; font-weight: 700;">{arb_value:.4f}</div>
                </div>
                <div style="color: #10b981; font-size: 1.1em; font-weight: 600;">💰 +${profit:.2f}</div>
                <div style="color: #8b5cf6; font-size: 0.9em;">{profit_pct:.1f}% ROI</div>
            </div>
            
            <!-- Home Team -->
            <div class="team-section">
                <img src="{TEAM_LOGOS.get(home, 'https://via.placeholder.com/120')}" class="team-image" onerror="this.style.display='none'">
                <div class="team-name">{home}</div>
                <div class="odds-display">
                    <div class="odds-label">Best Odds</div>
                    <div class="odds-value">{american_odds(best_odds.get(home, 0))}</div>
                </div>
            </div>
        </div>
        
        <!-- Sportsbooks Row -->
        <div class="divider"></div>
        <div style="margin-top: 20px;">
            <div style="color: #a0a0b0; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 15px;">📊 Best Odds by Sportsbook</div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px;">
    """, unsafe_allow_html=True)
    
    # Show top sportsbooks
    for i, (book_name, odds) in enumerate(all_bookmaker_odds.items()):
        if i >= 4:
            break
        st.markdown(f"""
                <div class="bookmaker-card">
                    <div class="bookmaker-name">{book_name}</div>
                    <div class="bookmaker-odds">{american_odds(odds)}</div>
                </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

# ============================================================================
# AUTHENTICATION PAGES
# ============================================================================

def page_auth():
    """Login and signup page for unauthenticated users"""
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">💰 CHEGY BETS</div>
        <div class="hero-subtitle">Professional Arbitrage Detection Across All Major Sports & Sportsbooks</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div style='text-align: center; margin-top: 40px;'></div>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            st.markdown("### Log In to Your Account")
            login_username = st.text_input("Username", key="login_user")
            login_password = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("🔓 Login", use_container_width=True):
                if login_username and login_password:
                    if login(login_username, login_password):
                        st.session_state.logged_in = True
                        st.session_state.username = login_username
                        st.session_state.user_tier = get_user_tier(login_username)
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please enter username and password")
            
            st.markdown("---")
            st.markdown("""
            **Test Account:**
            - Username: `admin`
            - Password: `chegy2024`
            """)
        
        with tab2:
            st.markdown("### Create New Account")
            signup_username = st.text_input("Choose Username", key="signup_user")
            signup_password = st.text_input("Choose Password", type="password", key="signup_pass")
            signup_tier = st.selectbox("Account Tier", ["free", "premium"], key="signup_tier")
            
            if st.button("✍️ Create Account", use_container_width=True):
                if signup_username and signup_password:
                    if len(signup_username) < 3:
                        st.error("❌ Username must be at least 3 characters")
                    elif signup_username == ADMIN_USERNAME:
                        st.error("❌ That username is reserved")
                    else:
                        users = load_users()
                        if signup_username in users:
                            st.error("❌ Username already taken")
                        else:
                            register_user(signup_username, signup_password, signup_tier)
                            st.success("✅ Account created! Please log in.")
                            st.session_state.logged_in = False
                else:
                    st.warning("⚠️ Please enter username and password")


def page_dashboard():
    """Main dashboard - only shown to authenticated users"""
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username.upper()}")
        st.markdown(f"**Tier:** {'👑 ADMIN' if st.session_state.user_tier == 'admin' else f'⭐ {st.session_state.user_tier.upper()}'}")
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_tier = None
            st.rerun()
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">💰 CHEGY BETS</div>
        <div class="hero-subtitle">Professional Arbitrage Detection Across All Major Sports & Sportsbooks</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Settings
    with st.sidebar:
        st.markdown("---")
        st.subheader("⚙️ Settings")
        
        # API Key - Admin Only
        if st.session_state.user_tier == "admin":
            api_key = st.text_input("API Key", value=os.environ.get('ODDS_API_KEY', ''), type='password')
        else:
            api_key = os.environ.get('ODDS_API_KEY', '')
            st.info("📌 Contact admin for API key access")
        
        if api_key:
            sports_map = get_available_sports(api_key)
            sport_name = st.selectbox("🏆 Sport", list(sports_map.keys()))
            sport = sports_map[sport_name]
        else:
            sport = "basketball_nba"
            if st.session_state.user_tier == "admin":
                st.warning("Add API key to unlock all sports")
        
        region = st.selectbox("🌍 Region", ["us", "eu", "uk"], index=0)
        
        st.markdown("**📊 Markets**")
        col_sel_all, col_desel_all = st.columns(2)
        with col_sel_all:
            select_all = st.button("✅ Select All", use_container_width=True, key="select_all_btn")
        with col_desel_all:
            deselect_all = st.button("❌ Deselect All", use_container_width=True, key="deselect_all_btn")
        
        if select_all:
            st.session_state.selected_markets = ["h2h", "spreads", "totals"]
        if deselect_all:
            st.session_state.selected_markets = []
        
        markets = st.multiselect(
            "Select Markets",
            ["h2h", "spreads", "totals"],
            default=st.session_state.get("selected_markets", ["h2h"]),
            key="markets_select"
        )
        st.session_state.selected_markets = markets
        
        if not markets:
            markets = ["h2h"]
        markets_str = ",".join(markets)
        
        stake = st.number_input("💵 Stake Amount", value=100.0, min_value=1.0, step=10.0)
        arb_threshold = st.number_input("🎯 Max Arb (%)", value=0.99, step=0.001, format="%.3f")
        
        if st.button("🔍 SEARCH ARBITRAGE", use_container_width=True):
            st.session_state.search = True

    # Check if search requested
    search = st.session_state.get("search", False)

    if not api_key:
        st.warning("🔑 Please provide The Odds API key in settings")
    elif search:
        with st.spinner("🔄 Scanning all sportsbooks..."):
            data = get_odds(api_key, sport, region, markets_str)
        
        if not data:
            st.markdown('<div class="badge-empty">❌ No games available</div>', unsafe_allow_html=True)
        else:
            save_detailed_odds(data)
            arbs = find_arbitrage(data)
            
            # Filter & build display
            opportunities = []
            for arb in arbs:
                if arb["arb_value"] > arb_threshold:
                    continue
                
                teams = arb["teams"]
                best = arb["odds"]
                team_names = list(best.keys())
                odds_vals = [best[team_names[0]], best[team_names[1]]]
                stake_a, stake_b, profit, profit_pct = compute_stakes(odds_vals[0], odds_vals[1], total=stake)
                
                # Collect all bookmaker odds
                all_bookmaker_odds = {}
                for game in data:
                    if game.get("teams") == teams:
                        for bm in game.get("bookmakers", []):
                            for market in bm.get("markets", []):
                                for outcome in market.get("outcomes", []):
                                    team = outcome.get("name")
                                    odds = outcome.get("price")
                                    if team == team_names[0]:
                                        all_bookmaker_odds[bm.get("title")] = odds
                
                opportunities.append({
                    "teams": teams,
                    "best_odds": best,
                    "all_odds": all_bookmaker_odds,
                    "arb_value": arb["arb_value"],
                    "profit": profit,
                    "profit_pct": profit_pct,
                    "stake_a": stake_a,
                    "stake_b": stake_b,
                })
            
            if not opportunities:
                st.markdown('<div class="badge-empty">❌ No arbitrage found. Try adjusting filters.</div>', unsafe_allow_html=True)
            else:
                # Show summary
                st.markdown(f'<div class="badge-success">✅ {len(opportunities)} ARBITRAGE OPPORTUNITIES FOUND</div>', unsafe_allow_html=True)
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{len(opportunities)}</div>
                        <div class="metric-label">Total Arbs</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    avg_profit = sum(o["profit"] for o in opportunities) / len(opportunities)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">${avg_profit:.2f}</div>
                        <div class="metric-label">Avg Profit</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    max_profit = max(o["profit"] for o in opportunities)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">${max_profit:.2f}</div>
                        <div class="metric-label">Max Profit</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col4:
                    avg_roi = sum(o["profit_pct"] for o in opportunities) / len(opportunities)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{avg_roi:.1f}%</div>
                        <div class="metric-label">Avg ROI</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Display opportunities
                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
                st.subheader("🎯 Available Opportunities")
                
                for opp in opportunities:
                    display_professional_game_card(
                        opp["teams"],
                        opp["best_odds"],
                        opp["all_odds"],
                        opp["arb_value"],
                        opp["profit"],
                        opp["profit_pct"]
                    )
                
                # Download option
                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
                df_export = pd.DataFrame([
                    {
                        "Game": " vs ".join(o["teams"]),
                        "Profit": f"${o['profit']:.2f}",
                        "ROI": f"{o['profit_pct']:.1f}%",
                        "Arb Value": f"{o['arb_value']:.4f}"
                    }
                    for o in opportunities
                ])
                
                csv = df_export.to_csv(index=False)
                st.download_button("📥 Export Results (CSV)", csv, "arbitrage_opportunities.csv", "text/csv", use_container_width=True)


# ============================================================================
# MAIN APP - Session State Check
# ============================================================================

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_tier = None
    st.session_state.selected_markets = ["h2h"]

# Show appropriate page based on login state
if not st.session_state.logged_in:
    page_auth()
else:
    page_dashboard()
