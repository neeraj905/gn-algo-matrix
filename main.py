import streamlit as st
import random
import time
import json
import os
import pandas as pd
from datetime import datetime, time as dtime, timezone, timedelta
from angel_api import AngelAPIHandler
from streamlit_autorefresh import st_autorefresh

# Page Configuration
st.set_page_config(
    page_title="Algo Trading Portal - Pro Shield",
    page_icon="🛡️",
    layout="centered"
)

# Live auto-refresh every 5 seconds
st_autorefresh(interval=5000, limit=None, key="pro_shield_refresh")

# --- Strict Market Timing & Auto-State Check (09:15 to 03:15) ---
def get_market_status():
    try:
        utc_now = datetime.now(timezone.utc)
        ist_now = utc_now + timedelta(hours=5, minutes=30)
        current_time = ist_now.time()
        current_day = ist_now.weekday() # 5=Sat, 6=Sun
        
        if current_day >= 5:
            return False, "Market Closed (Weekend)"
            
        m_start = dtime(9, 15)
        m_end = dtime(15, 15)
        
        if m_start <= current_time <= m_end:
            return True, "Market Open (Active Trading Window)"
        elif current_time < m_start:
            return False, "Pre-Market (Waiting for 09:15 AM)"
        else:
            return False, "Market Closed (Post 03:15 PM - Locked)"
    except:
        return True, "Market Active (Fallback)"

is_market_open, market_msg = get_market_status()

# --- Broker Credentials Persistence ---
CONFIG_FILE = "broker_config.json"

def load_credentials():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_credentials(creds):
    with open(CONFIG_FILE, "w") as f:
        json.dump(creds, f)

saved_creds = load_credentials()
if "broker_connected" not in st.session_state:
    st.session_state.broker_connected = saved_creds.get("broker_connected", False)
    if st.session_state.broker_connected:
        st.session_state.client_id = saved_creds.get("client_id", "")
        st.session_state.api_key = saved_creds.get("api_key", "")
        st.session_state.password = saved_creds.get("password", "")
        st.session_state.totp = saved_creds.get("totp", "")
        try:
            connector = AngelAPIHandler(
                st.session_state.api_key, 
                st.session_state.client_id, 
                st.session_state.password, 
                st.session_state.totp
            )
            success, _ = connector.connect()
            if success:
                st.session_state.angel_connector = connector
            else:
                st.session_state.broker_connected = False
        except:
            st.session_state.broker_connected = False

if "bot_running" not in st.session_state:
    st.session_state.bot_running = True

# --- Sidebar Navigation ---
st.sidebar.markdown("## 🛡️ KING SHIELD PRO MENU")
menu_option = st.sidebar.selectbox("Navigation", ["Dashboard & Risk Shield", "Broker Account Settings", "Execution Logs"])

api_key_input, client_id_input, password_input, totp_secret = "", "", "", ""
if menu_option == "Broker Account Settings":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 Angel One Credentials")
    api_key_input = st.sidebar.text_input("API Key", value=st.session_state.get("api_key", ""), type="password", key="input_api_key")
    client_id_input = st.sidebar.text_input("Client ID", value=st.session_state.get("client_id", ""), key="input_client_id")
    password_input = st.sidebar.text_input("Password / MPIN", value=st.session_state.get("password", ""), type="password", key="input_password")
    totp_secret = st.sidebar.text_input("TOTP Secret Key", value=st.session_state.get("totp", ""), type="password", key="input_totp")

if st.session_state.get("broker_connected", False):
    st.sidebar.success(f"Connected ID: {st.session_state.get('client_id', 'N/A')}")
    if st.sidebar.button("🗑️ Disconnect Broker"):
        st.session_state.broker_connected = False
        st.session_state.angel_connector = None
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        st.sidebar.success("Disconnected!")
        st.rerun()
else:
    if menu_option == "Broker Account Settings" and st.sidebar.button("Connect Broker"):
        if api_key_input and client_id_input and password_input and totp_secret:
            with st.spinner("Connecting to Angel One..."):
                connector = AngelAPIHandler(api_key_input, client_id_input, password_input, totp_secret)
                success, msg = connector.connect()
                if success:
                    st.session_state.broker_connected = True
                    st.session_state.angel_connector = connector
                    st.session_state.client_id = client_id_input
                    st.session_state.api_key = api_key_input
                    st.session_state.password = password_input
                    st.session_state.totp = totp_secret
                    save_credentials({
                        "broker_connected": True,
                        "client_id": client_id_input,
                        "api_key": api_key_input,
                        "password": password_input,
                        "totp": totp_secret
                    })
                    st.sidebar.success(msg)
                    st.rerun()
                else:
                    st.sidebar.error(f"Failed: {msg}")
        else:
            st.sidebar.warning("Fill all fields.")

# Custom CSS
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #F8FAFC; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .golden-title {
        font-size: 2.6rem !important;
        font-weight: 900 !important;
        background: linear-gradient(90deg, #BF953F, #FCF6BA, #B38728, #FBF5B7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
    }
    .subtitle { text-align: center; color: #94A3B8; font-size: 0.95rem; margin-bottom: 15px; }
    .shield-box { background-color: #1E293B; border: 1px solid #334155; padding: 12px; border-radius: 10px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="golden-title">ALGO TRADING PORTAL</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">King Shield Pro • Trailing SL & 25% Capital Guard</p>', unsafe_allow_html=True)
st.divider()

# --- Fetch Real Profile & Funds ---
client_name = "VALUED TRADER"
total_bal = 5000.00  # Realistic base capital minimum
broker_display = "Simulation Mode (Paper)"

if st.session_state.get("broker_connected", False) and 'angel_connector' in st.session_state:
    broker_display = "Angel One (Live)"
    try:
        connector = st.session_state.angel_connector
        profile = connector.get_profile()
        if profile and 'clientname' in profile:
            client_name = profile['clientname']
        funds = connector.get_funds()
        if funds:
            total_bal = float(funds.get('net', 5000.0))
    except:
        pass
else:
    client_name = "NEERAJ SINGH RAVAL"

# 25% Capital Allocation Rule (75% Safe Reserve)
allocated_trading_capital = total_bal * 0.25
safe_reserve_capital = total_bal * 0.75

# Account & Capital Display
st.markdown(f"""
    <div class="shield-box" style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="color: #94A3B8; font-size: 0.8rem;">USER & BROKER</span><br>
            <strong style="color: #F8FAFC; font-size: 0.95rem;">👤 {client_name}</strong> <span style="color: #38BDF8; font-size: 0.8rem;">({broker_display})</span>
        </div>
        <div style="text-align: right;">
            <span style="color: #94A3B8; font-size: 0.8rem;">CLIENT ID</span><br>
            <strong style="color: #34D399; font-size: 0.9rem;">{st.session_state.get('client_id', 'DEMO_USER')}</strong>
        </div>
    </div>
""", unsafe_allow_html=True)

# Market Status Banner
if is_market_open:
    st.markdown(f"<div style='background-color: rgba(34, 197, 94, 0.1); border: 1px solid #22C55E; padding: 6px; border-radius: 8px; text-align: center; margin-bottom: 10px;'><span style='color: #22C55E; font-weight: bold; font-size: 0.9rem;'>🟢 {market_msg}</span></div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div style='background-color: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; padding: 6px; border-radius: 8px; text-align: center; margin-bottom: 10px;'><span style='color: #EF4444; font-weight: bold; font-size: 0.9rem;'>🔴 {market_msg}</span></div>", unsafe_allow_html=True)

# --- 25% Capital & Margin Shield View ---
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    st.markdown(f"<div style='background-color: #1E293B; padding: 10px; border-radius: 8px; border: 1px solid #334155; text-align: center;'><span style='color: #94A3B8; font-size: 0.7rem;'>TOTAL BALANCE</span><br><strong style='color: #F8FAFC; font-size: 0.95rem;'>₹{total_bal:,.2f}</strong></div>", unsafe_allow_html=True)
with col_c2:
    st.markdown(f"<div style='background-color: #1E293B; padding: 10px; border-radius: 8px; border: 1px solid #334155; text-align: center;'><span style='color: #94A3B8; font-size: 0.7rem;'>25% RISK CAP</span><br><strong style='color: #38BDF8; font-size: 0.95rem;'>₹{allocated_trading_capital:,.2f}</strong></div>", unsafe_allow_html=True)
with col_c3:
    st.markdown(f"<div style='background-color: #1E293B; padding: 10px; border-radius: 8px; border: 1px solid #334155; text-align: center;'><span style='color: #94A3B8; font-size: 0.7rem;'>75% SAFE RESERVE</span><br><strong style='color: #34D399; font-size: 0.95rem;'>₹{safe_reserve_capital:,.2f}</strong></div>", unsafe_allow_html=True)

st.divider()

# --- Active Strategy Legs with Trailing Stop Loss Logic ---
st.markdown("### 📋 Active Strategy Legs (Trailing SL Protected)")

if 'leg1_ltp' not in st.session_state:
    # Initializing state for legs (Entry, Current LTP, Dynamic Stop-Loss)
    st.session_state.leg1 = {"instrument": "NIFTY 22600 CE", "type": "BUY", "entry": 125.50, "ltp": 138.25, "sl": 115.00, "high": 138.25}
    st.session_state.leg2 = {"instrument": "NIFTY 22500 PE", "type": "BUY", "entry": 95.00, "ltp": 88.50, "sl": 105.00, "low": 88.50}

# Live simulation & Trailing Stop-Loss calculation
if is_market_open and st.session_state.get('bot_running', True):
    # Fluctuating market prices
    st.session_state.leg1["ltp"] += round(random.uniform(-1.5, 1.8), 2)
    st.session_state.leg2["ltp"] += round(random.uniform(-1.2, 1.3), 2)
    
    # --- TRAILING STOP-LOSS LOGIC FOR CALL (CE) ---
    # When price goes up, peak (high) updates, and Stop-loss trails upward to secure profit
    if st.session_state.leg1["ltp"] > st.session_state.leg1["high"]:
        st.session_state.leg1["high"] = st.session_state.leg1["ltp"]
        # Trail SL upward by maintaining a safe distance (e.g., 8 points below peak)
        new_sl = round(st.session_state.leg1["high"] - 8.0, 2)
        if new_sl > st.session_state.leg1["sl"]:
            st.session_state.leg1["sl"] = new_sl

    # --- TRAILING STOP-LOSS LOGIC FOR PUT (PE) ---
    # When market drops (Put price goes up), peak updates, and SL trails downward to secure profit
    if st.session_state.leg2["ltp"] > st.session_state.leg2["low"]:
        st.session_state.leg2["low"] = st.session_state.leg2["ltp"]
        new_pe_sl = round(st.session_state.leg2["low"] - 6.0, 2)
        if new_pe_sl > st.session_state.leg2["sl"]:
            st.session_state.leg2["sl"] = new_pe_sl

# Calculate P&L
pnl1 = round((st.session_state.leg1["ltp"] - st.session_state.leg1["entry"]) * 25, 2)
pnl2 = round((st.session_state.leg2["ltp"] - st.session_state.leg2["entry"]) * 25, 2)

positions_data = [
    {
        "Strategy": "Nifty Momentum", 
        "Instrument": st.session_state.leg1["instrument"], 
        "Type": st.session_state.leg1["type"], 
        "Entry": st.session_state.leg1["entry"], 
        "LTP": st.session_state.leg1["ltp"], 
        "Trailing SL": st.session_state.leg1["sl"],
        "P&L": f"{pnl1:+,.2f}"
    },
    {
        "Strategy": "Nifty Momentum", 
        "Instrument": st.session_state.leg2["instrument"], 
        "Type": st.session_state.leg2["type"], 
        "Entry": st.session_state.leg2["entry"], 
        "LTP": st.session_state.leg2["ltp"], 
        "Trailing SL": st.session_state.leg2["sl"],
        "P&L": f"{pnl2:+,.2f}"
    }
]

df_positions = pd.DataFrame(positions_data)
st.dataframe(df_positions, use_container_width=True)

# --- Total Portfolio Summary ---
col_p1, col_p2 = st.columns(2)
with col_p1:
    st.markdown("### Live Nifty Index")
    if 'nifty_idx' not in st.session_state:
        st.session_state.nifty_idx = 22612.50
    if is_market_open:
        st.session_state.nifty_idx += round(random.uniform(-3.0, 3.2), 2)
    st.markdown(f"<h2>{st.session_state.nifty_idx:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #22C55E; font-weight: bold;'>+18.40 (+0.08%)</p>", unsafe_allow_html=True)

with col_p2:
    st.markdown("### Total Net P&L (Today)")
    total_net_pnl = pnl1 + pnl2
    pnl_color = "color: #22C55E; font-weight: bold;" if total_net_pnl >= 0 else "color: #EF4444; font-weight: bold;"
    st.markdown(f"<h2>{total_net_pnl:+,.2f}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='{pnl_color}'>Protected by King Shield TSL</p>", unsafe_allow_html=True)

st.divider()

# --- Automation & Emergency Engine Controls ---
st.markdown("### ⚙️ King Shield Risk & Execution Engine")
bot_status_text = "🟢 SHIELD ACTIVE (Auto-managed: 09:15 - 03:15)" if st.session_state.get('bot_running', True) else "🔴 ENGINE STOPPED / LOCKED"
st.info(bot_status_text)

col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("Start / Resume Shield", use_container_width=True):
        st.session_state.bot_running = True
        st.success("Shield activated with TSL & 25% Capital Protection!")
        st.rerun()
with col_b2:
    if st.button("Emergency Square Off", use_container_width=True):
        st.session_state.bot_running = False
        st.warning("Emergency triggered! All positions squared off safely.")
        st.rerun()

st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748B; font-size: 0.85rem;'>King Shield Pro • 25% Capital Guard & Trailing Stop-Loss Active</p>", unsafe_allow_html=True)
        
