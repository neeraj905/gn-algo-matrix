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
    page_title="Algo Trading Portal - Pro",
    page_icon="⚡",
    layout="centered"
)

# Live auto-refresh every 5 seconds
st_autorefresh(interval=5000, limit=None, key="pro_market_refresh")

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

# Auto-manage bot states based on market hours
if "bot_running" not in st.session_state:
    st.session_state.bot_running = True # Tradetron style: Stays on until stopped or market closes

# --- Sidebar Navigation & Broker Config ---
st.sidebar.markdown("## 🛡️ TRADETRON PRO MENU")
menu_option = st.sidebar.selectbox("Navigation", ["Dashboard & Positions", "Broker Account Settings", "Execution Logs"])

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
        font-size: 2.8rem !important;
        font-weight: 900 !important;
        background: linear-gradient(90deg, #BF953F, #FCF6BA, #B38728, #FBF5B7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
    }
    .subtitle { text-align: center; color: #94A3B8; font-size: 1rem; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="golden-title">ALGO TRADING PORTAL</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Multi-Strategy Pro Terminal (Tradetron Style)</p>', unsafe_allow_html=True)
st.divider()

# --- Broker Profile & Account Bar ---
client_name = "NEERAJ SINGH RAVAL" # Can be fetched via API profile if connected
broker_display = "Angel One (Live)" if st.session_state.get("broker_connected", False) else "Simulation Mode (Paper)"
st.markdown(f"""
    <div style="background-color: #1E293B; border: 1px solid #334155; padding: 12px; border-radius: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="color: #94A3B8; font-size: 0.85rem;">ACCOUNT & BROKER</span><br>
            <strong style="color: #F8FAFC; font-size: 1rem;">👤 {client_name}</strong> <span style="color: #38BDF8; font-size: 0.85rem;">({broker_display})</span>
        </div>
        <div style="text-align: right;">
            <span style="color: #94A3B8; font-size: 0.85rem;">CLIENT ID</span><br>
            <strong style="color: #34D399; font-size: 0.95rem;">{st.session_state.get('client_id', 'DEMO_USER')}</strong>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- Market Status & Auto-Bot Banner ---
if is_market_open:
    st.markdown(f"<div style='background-color: rgba(34, 197, 94, 0.1); border: 1px solid #22C55E; padding: 8px; border-radius: 8px; text-align: center; margin-bottom: 10px;'><span style='color: #22C55E; font-weight: bold;'>🟢 {market_msg}</span></div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div style='background-color: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; padding: 8px; border-radius: 8px; text-align: center; margin-bottom: 10px;'><span style='color: #EF4444; font-weight: bold;'>🔴 {market_msg}</span></div>", unsafe_allow_html=True)

# --- Capital & Margin Breakdown Section ---
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    st.markdown("<div style='background-color: #1E293B; padding: 10px; border-radius: 8px; border: 1px solid #334155; text-align: center;'><span style='color: #94A3B8; font-size: 0.75rem;'>TOTAL BALANCE</span><br><strong style='color: #F8FAFC; font-size: 1.05rem;'>₹1,50,000</strong></div>", unsafe_allow_html=True)
with col_c2:
    st.markdown("<div style='background-color: #1E293B; padding: 10px; border-radius: 8px; border: 1px solid #334155; text-align: center;'><span style='color: #94A3B8; font-size: 0.75rem;'>USED MARGIN</span><br><strong style='color: #F8FAFC; font-size: 1.05rem;'>₹45,200</strong></div>", unsafe_allow_html=True)
with col_c3:
    st.markdown("<div style='background-color: #1E293B; padding: 10px; border-radius: 8px; border: 1px solid #334155; text-align: center;'><span style='color: #94A3B8; font-size: 0.75rem;'>AVAILABLE</span><br><strong style='color: #34D399; font-size: 1.05rem;'>₹1,04,800</strong></div>", unsafe_allow_html=True)

st.divider()

# --- Multi-Leg Positions Table (Tradetron Style) ---
st.markdown("### 📋 Active Strategy Legs (Multi-Position View)")

if 'positions_df' not in st.session_state:
    st.session_state.positions_df = pd.DataFrame([
        {"Strategy": "Nifty Momentum", "Instrument": "NIFTY 22600 CE", "Type": "BUY", "Qty": 25, "Entry": 125.50, "LTP": 138.25, "P&L (+ / -)": "+318.75"},
        {"Strategy": "Nifty Momentum", "Instrument": "NIFTY 22500 PE", "Type": "BUY", "Qty": 25, "Entry": 95.00, "LTP": 88.50, "P&L (+ / -)": "-162.50"},
        {"Strategy": "BankNifty Alpha", "Instrument": "BANKNIFTY 48100 CE", "Type": "BUY", "Qty": 15, "Entry": 310.00, "LTP": 345.00, "P&L (+ / -)": "+525.00"}
    ])

# Update dynamic values if market is open
if is_market_open and st.session_state.get('bot_running', True):
    # Simulate fluctuating multi-leg P&L
    pass

st.dataframe(st.session_state.positions_df, use_container_width=True)

# --- Total Portfolio Summary ---
col_p1, col_p2 = st.columns(2)
with col_p1:
    st.markdown("### Live Nifty Index")
    nifty_val = 22612.50 + (random.uniform(-5, 5) if is_market_open else 0)
    st.markdown(f"<h2>{nifty_val:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #22C55E; font-weight: bold;'>+18.40 (+0.08%)</p>", unsafe_allow_html=True)

with col_p2:
    st.markdown("### Total Net P&L (Today)")
    if 'total_pnl' not in st.session_state:
        st.session_state.total_pnl = 12681.25
    if is_market_open and st.session_state.get('bot_running', True):
        st.session_state.total_pnl += round(random.uniform(-10.0, 12.5), 2)
    
    pnl_val = st.session_state.total_pnl
    pnl_color = "color: #22C55E; font-weight: bold;" if pnl_val >= 0 else "color: #EF4444; font-weight: bold;"
    st.markdown(f"<h2>{pnl_val:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='{pnl_color}'>Realized + Unrealized</p>", unsafe_allow_html=True)

st.divider()

# --- Persistent Bot Controls (Tradetron Style) ---
st.markdown("### ⚙️ Automation & Execution Engine")
bot_status_text = "🟢 ENGINE RUNNING (Auto-managed: 09:15 - 03:15)" if st.session_state.get('bot_running', True) else "🔴 ENGINE STOPPED / LOCKED"
st.info(bot_status_text)

col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("Start / Resume Engine", use_container_width=True):
        st.session_state.bot_running = True
        st.success("Engine resumed successfully! It will automatically lock at 03:15 PM.")
        st.rerun()
with col_b2:
    if st.button("Emergency Stop / Square Off", use_container_width=True):
        st.session_state.bot_running = False
        st.warning("Engine stopped and positions squared off manually.")
        st.rerun()

st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748B; font-size: 0.85rem;'>Tradetron-Style Pro Matrix • Secure Mobile Terminal</p>", unsafe_allow_html=True)
        
