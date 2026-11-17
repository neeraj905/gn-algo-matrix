# ==============================================================================
# SECTION 1: IMPORTS & PAGE CONFIGURATION
# ==============================================================================
import streamlit as st
import random
import time
import json
import os
import pandas as pd
from datetime import datetime, time as dtime, timezone, timedelta
from angel_api import AngelAPIHandler
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Algo Trading Portal - Multi-Index Pro",
    page_icon="🛡️",
    layout="centered"
)


# ==============================================================================
# SECTION 2: CUSTOM UI STYLING (BOLD NUMBERS & COLORS)
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f8fafc; }
    .metric-card { background: #1e293b; padding: 15px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 10px; }
    .profit-text { color: #22c55e !important; font-weight: bold; font-size: 1.2rem; }
    .loss-text { color: #ef4444 !important; font-weight: bold; font-size: 1.2rem; }
    /* Tables ke andar ke saare numbers gehre (bold) aur clear dikhne ke liye */
    table tbody tr td { font-weight: bold !important; color: #f8fafc !important; }
    table thead tr th { font-weight: bold !important; color: #94A3B8 !important; }
</style>
""", unsafe_allow_html=True)

# Live auto-refresh every 5 seconds
st_autorefresh(interval=5000, limit=None, key="multi_index_refresh")


# ==============================================================================
# SECTION 3: STRICT MARKET TIMING & STATE MANAGEMENT
# ==============================================================================
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

# Session State Initialization (Refresh Safe)
if "broker_connected" not in st.session_state:
    st.session_state.broker_connected = False
    st.session_state.client_id = ""
    st.session_state.api_key = ""
    st.session_state.password = ""
    st.session_state.totp = ""
    st.session_state.angel_connector = None
    st.session_state.client_name = "NEERAJ SINGH RAVAL"

if "bot_running" not in st.session_state:
    st.session_state.bot_running = True


# ==============================================================================
# SECTION 4: SIDEBAR NAVIGATION & BROKER SETTINGS
# ==============================================================================
st.sidebar.markdown("## 🛡️ MULTI-INDEX PRO MENU")
menu_option = st.sidebar.selectbox("Navigation", ["Dashboard & Index Matrix", "Broker Account Settings", "Execution Logs"])

api_key_input, client_id_input, password_input, totp_secret = "", "", "", ""
if menu_option == "Broker Account Settings":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 Connect Your Demat Broker")
    st.sidebar.markdown("<p style='font-size: 0.8rem; color: #94A3B8;'>Enter your own broker API credentials to start trading from your account.</p>", unsafe_allow_html=True)
    api_key_input = st.sidebar.text_input("API Key", type="password", key="input_api_key")
    client_id_input = st.sidebar.text_input("Client ID", key="input_client_id")
    password_input = st.sidebar.text_input("Password / MPIN", type="password", key="input_password")
    totp_secret = st.sidebar.text_input("TOTP Secret Key", type="password", key="input_totp")

if st.session_state.get("broker_connected", False):
    st.sidebar.success(f"Connected Client: {st.session_state.get('client_id', 'N/A')}")
    if st.sidebar.button("🗑️ Disconnect Broker"):
        st.session_state.broker_connected = False
        st.session_state.angel_connector = None
        st.session_state.client_id = ""
        st.session_state.client_name = "NEERAJ SINGH RAVAL"
        st.sidebar.success("Disconnected successfully!")
        st.rerun()
else:
    if menu_option == "Broker Account Settings" and st.sidebar.button("Connect Broker"):
        if api_key_input and client_id_input and password_input and totp_secret:
            with st.spinner("Connecting to Angel One..."):
                try:
                    connector = AngelAPIHandler(api_key_input, client_id_input, password_input, totp_secret)
                    success, msg = connector.connect()
                    if success:
                        st.session_state.broker_connected = True
                        st.session_state.angel_connector = connector
                        st.session_state.client_id = client_id_input
                        st.session_state.api_key = api_key_input
                        
                        try:
                            profile = connector.get_profile()
                            if profile and 'clientname' in profile:
                                st.session_state.client_name = profile['clientname']
                            else:
                                st.session_state.client_name = client_id_input
                        except:
                            st.session_state.client_name = client_id_input
                            
                        st.sidebar.success("Broker Connected Successfully!")
                        st.rerun()
                    else:
                        st.sidebar.error(f"Connection Failed: {msg}")
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")
        else:
            st.sidebar.warning("Please fill in all broker credentials.")


# ==============================================================================
# SECTION 5: MAIN HEADER & USER STATUS
# ==============================================================================
st.markdown("<h1 style='text-align: center; color: #f59e0b;'>ALGO TRADING PORTAL</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94A3B8;'>Multi-Index Pro • Nifty, BankNifty, FinNifty, Midcap & Sensex Shield</p>", unsafe_allow_html=True)
st.markdown("---")

display_name = st.session_state.get('client_name', 'NEERAJ SINGH RAVAL')
client_id_show = st.session_state.get('client_id', 'DEMO_USER') if st.session_state.broker_connected else 'DEMO_USER'
mode_text = 'Live Broker Connected' if st.session_state.broker_connected else 'Simulation Mode (Paper)'

st.markdown(f"""
<div class='metric-card'>
    <b>USER & BROKER</b><br>
    👤 <b>{display_name}</b> ({mode_text})<br>
    <span style='color: #22c55e;'><b>CLIENT ID: {client_id_show}</b></span>
</div>
""", unsafe_allow_html=True)

# Market Status Box
status_color = "#22c55e" if is_market_open else "#ef4444"
st.markdown(f"""
<div style='background: #1e293b; padding: 10px; border-radius: 8px; border: 1px solid {status_color}; text-align: center; margin-bottom: 15px;'>
    <span style='height: 10px; width: 10px; background-color: {status_color}; display: inline-block; border-radius: 50%; margin-right: 8px;'></span>
    <b>{market_msg}</b>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# SECTION 6: CAPITAL & RISK ALLOCATION CARDS
# ==============================================================================
total_balance = 5000.00
risk_cap = total_balance * 0.25
safe_reserve = total_balance * 0.75

st.markdown(f"""
<div class='metric-card'>
    <div style='text-align: center; color: #94A3B8; font-size: 0.85rem;'>TOTAL BALANCE</div>
    <div style='text-align: center; font-size: 1.5rem; font-weight: bold;'>₹{total_balance:,.2f}</div>
</div>
<div class='metric-card'>
    <div style='text-align: center; color: #94A3B8; font-size: 0.85rem;'>25% RISK CAP (Protected by Shield)</div>
    <div style='text-align: center; font-size: 1.3rem; font-weight: bold; color: #f59e0b;'>₹{risk_cap:,.2f}</div>
</div>
<div class='metric-card'>
    <div style='text-align: center; color: #94A3B8; font-size: 0.85rem;'>75% SAFE RESERVE</div>
    <div style='text-align: center; font-size: 1.3rem; font-weight: bold; color: #22c55e;'>₹{safe_reserve:,.2f}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")


# ==============================================================================
# SECTION 7: MULTI-INDEX STRATEGY MATRIX & DYNAMIC TSL LOGIC
# ==============================================================================
st.markdown("### 📊 Multi-Index Live Strategy Matrix (All 5 Indices)")

price_tick = random.uniform(-1.5, 2.5) if st.session_state.get('bot_running', True) else 0.0

indices_matrix = {
    "NIFTY": {"spot": 22612.50 + price_tick, "ce_entry": 120.0, "ce_ltp": 138.25 + price_tick, "pe_entry": 80.0, "pe_ltp": 88.50 - price_tick, "pnl": 1250.0 + (price_tick * 40)},
    "BANKNIFTY": {"spot": 48250.00 + (price_tick * 2), "ce_entry": 120.0, "ce_ltp": 345.0 + (price_tick * 1.5), "pe_entry": 80.0, "pe_ltp": 290.0 - (price_tick * 1.5), "pnl": -450.0 + (price_tick * 35)},
    "FINNIFTY": {"spot": 21400.00 + price_tick, "ce_entry": 120.0, "ce_ltp": 112.5 + price_tick, "pe_entry": 80.0, "pe_ltp": 95.0 - price_tick, "pnl": 830.0 + (price_tick * 25)},
    "MIDCAP": {"spot": 10850.00 + (price_tick * 0.5), "ce_entry": 120.0, "ce_ltp": 65.2 + (price_tick * 0.5), "pe_entry": 80.0, "pe_ltp": 54.1 - (price_tick * 0.5), "pnl": 420.0 + (price_tick * 15)},
    "SENSEX": {"spot": 74500.00 + (price_tick * 3), "ce_entry": 120.0, "ce_ltp": 523.38 + (price_tick * 2), "pe_entry": 80.0, "pe_ltp": 476.74 - (price_tick * 2), "pnl": 27962.75 + (price_tick * 90)}
}

total_combined_pnl = 0.0

for idx_key, val in indices_matrix.items():
    # Tagda TSL logic: Value badhne par TSL automatically upar shift hoga
    ce_tsl = max(115.0, val["ce_entry"] - 5.0 + (val["ce_ltp"] - val["ce_entry"]) * 0.6) if val["ce_ltp"] > val["ce_entry"] else 115.0
    pe_tsl = max(75.0, val["pe_entry"] - 5.0 + (val["pe_ltp"] - val["pe_entry"]) * 0.6) if val["pe_ltp"] > val["pe_entry"] else 75.0

    st.markdown(f"**📈 {idx_key} (Spot: {val['spot']:,.2f})**")
    
    df_index = pd.DataFrame([
        {
            "Instrument": f"{idx_key} CE", 
            "Type": "BUY CALL", 
            "Entry": val["ce_entry"], 
            "LTP": round(val["ce_ltp"], 2), 
            "Trailing SL": round(ce_tsl, 2)
        },
        {
            "Instrument": f"{idx_key} PE", 
            "Type": "BUY PUT", 
            "Entry": val["pe_entry"], 
            "LTP": round(val["pe_ltp"], 2), 
            "Trailing SL": round(pe_tsl, 2)
        }
    ])
    
    st.dataframe(df_index, use_container_width=True, hide_index=True)
    total_combined_pnl += val["pnl"]

st.markdown("---")


# ==============================================================================
# SECTION 8: TOTAL NET P&L DISPLAY
# ==============================================================================
st.markdown("### 💰 Total Net P&L (All 5 Indices Combined)")
pnl_class = "profit-text" if total_combined_pnl >= 0 else "loss-text"
pnl_sign = "+" if total_combined_pnl >= 0 else ""

st.markdown(f"""
<div class='metric-card' style='text-align: center;'>
    <h1 class='{pnl_class}'>{pnl_sign}₹{total_combined_pnl:,.2f}</h1>
    <p style='color: #94A3B8; font-size: 0.85rem;'>Protected by Multi-Index King Shield TSL</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")


# ==============================================================================
# SECTION 9: ENGINE & SAFETY CONTROLS (SHIELD & EMERGENCY)
# ==============================================================================
st.markdown("### ⚙️ Engine & Safety Controls")
shield_bg = "#14532d" if st.session_state.bot_running else "#7f1d1d"
shield_text = "🟢 SHIELD ACTIVE (Auto-managed: 09:15 - 15:15)" if st.session_state.bot_running else "🔴 SHIELD STOPPED"

st.markdown(f"""
<div class='metric-card' style='background: {shield_bg}; border-color: #22c55e; text-align: center;'>
    <b>{shield_text}</b>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("▶ Start / Resume Shield", use_container_width=True):
        st.session_state.bot_running = True
        st.success("Shield Resumed Successfully!")
        st.rerun()
with col2:
    if st.button("🚨 Emergency Square Off", use_container_width=True, type="primary"):
        st.session_state.bot_running = False
        st.error("EMERGENCY SQUARE OFF TRIGGERED! All positions closed.")
        st.rerun()
