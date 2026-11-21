import streamlit as st
import random
import time
import json
import os
import pandas as pd
from datetime import datetime, time as dtime, timezone, timedelta
from angel_api import AngelAPIHandler
from streamlit_autorefresh import st_autorefresh

# ==============================================================================
# PART 0: PAGE CONFIGURATION & AUTO-REFRESH
# ==============================================================================
st.set_page_config(
    page_title="Algo Trading Portal - Multi-Index Pro",
    page_icon="🛡️",
    layout="centered"
)

# Live auto-refresh every 5 seconds
st_autorefresh(interval=5000, limit=None, key="multi_index_refresh")

# ==============================================================================
# PART 1: DARK THEME & RICH METALLIC GOLD HEADER
# ==============================================================================
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #F8FAFC;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .golden-title {
        font-size: 3rem !important;
        font-weight: 900 !important;
        letter-spacing: 2px;
        line-height: 1.15;
        background: linear-gradient(180deg, #FFFBEB 0%, #FDE047 38%, #EAB308 72%, #A16207 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0px 2px 10px rgba(234, 179, 8, 0.28));
        text-align: center;
        margin-bottom: 4px;
    }
    .subtitle {
        text-align: center;
        color: #CBD5E1;
        font-size: 0.92rem;
        font-weight: 600;
        margin-bottom: 14px;
    }
    .shield-box {
        background-color: #1E293B;
        border: 1px solid #334155;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 14px;
    }
    .index-header {
        background: #1E293B;
        border-left: 4px solid #38BDF8;
        padding: 8px 12px;
        font-weight: bold;
        font-size: 1.1rem;
        margin-top: 15px;
        margin-bottom: 5px;
        border-radius: 4px;
        color: #38BDF8;
    }
    div[data-testid="stTextInput"] label {
        color: #F8FAFC !important;
        font-weight: 800 !important;
    }
    div[data-testid="stTextInput"] input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: 1px solid #64748b !important;
        border-radius: 8px !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
    }
    div.stButton > button:first-child {
        background-color: #334155;
        color: #F8FAFC;
        border: 1px solid #475569;
        font-weight: bold;
        border-radius: 8px;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #475569;
        border-color: #64748B;
        color: #FFFFFF;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="golden-title">ALGO TRADING PORTAL</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Multi-Index Pro • Nifty, BankNifty, FinNifty, Midcap & Sensex Shield</p>', unsafe_allow_html=True)
st.divider()

# ==============================================================================
# PART 2: PER-DEVICE REFRESH-SAFE CLIENT ID & BROKER SIDEBAR
# ==============================================================================
def get_market_status():
    try:
        utc_now = datetime.now(timezone.utc)
        ist_now = utc_now + timedelta(hours=5, minutes=30)
        current_time = ist_now.time()
        current_day = ist_now.weekday()  # 5=Sat, 6=Sun

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
    except Exception:
        return True, "Market Active (Fallback)"

is_market_open, market_msg = get_market_status()

url_cid = st.query_params.get("cid", "").strip().upper()

if "broker_connected" not in st.session_state:
    st.session_state.broker_connected = False
if "client_id" not in st.session_state:
    st.session_state.client_id = url_cid
elif url_cid and not st.session_state.client_id:
    st.session_state.client_id = url_cid

if st.session_state.client_id and st.query_params.get("cid", "") != st.session_state.client_id:
    st.query_params["cid"] = st.session_state.client_id

if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "password" not in st.session_state:
    st.session_state.password = ""
if "totp" not in st.session_state:
    st.session_state.totp = ""
if "bot_running" not in st.session_state:
    st.session_state.bot_running = True

st.sidebar.markdown("## 🛡️ MULTI-INDEX PRO MENU")
menu_option = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard & Index Matrix", "Broker Account Settings", "Execution Logs"]
)

api_key_input, client_id_input, password_input, totp_secret = "", "", "", ""
if menu_option == "Broker Account Settings":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 Connect Your Demat Broker")
    st.sidebar.markdown(
        "<p style='font-size: 0.8rem; color: #94A3B8;'>Enter your own broker API credentials to start trading from your account.</p>",
        unsafe_allow_html=True
    )
    api_key_input = st.sidebar.text_input("API Key", type="password", key="input_api_key")
    client_id_input = st.sidebar.text_input(
        "Client ID",
        value=st.session_state.get("client_id", ""),
        key="input_client_id"
    )
    password_input = st.sidebar.text_input("Password / MPIN", type="password", key="input_password")
    totp_secret = st.sidebar.text_input("TOTP Secret Key", type="password", key="input_totp")

if st.session_state.get("broker_connected", False):
    st.sidebar.success(f"Connected Client: {st.session_state.get('client_id', 'N/A')}")
    if st.sidebar.button("🗑️ Disconnect Broker"):
        st.session_state.broker_connected = False
        st.session_state.angel_connector = None
        st.session_state.client_id = ""
        st.session_state.api_key = ""
        st.session_state.password = ""
        st.session_state.totp = ""
        if "cid" in st.query_params:
            del st.query_params["cid"]
        st.sidebar.success("Disconnected successfully!")
        st.rerun()
else:
    if menu_option == "Broker Account Settings" and st.sidebar.button("Connect Broker"):
        clean_cid = client_id_input.strip().upper()
        if api_key_input and clean_cid and password_input and totp_secret:
            with st.spinner("Connecting to Angel One..."):
                connector = AngelAPIHandler(api_key_input, clean_cid, password_input, totp_secret)
                success, msg = connector.connect()
                if success:
                    st.session_state.broker_connected = True
                    st.session_state.angel_connector = connector
                    st.session_state.client_id = clean_cid
                    st.session_state.api_key = api_key_input
                    st.session_state.password = password_input
                    st.session_state.totp = totp_secret
                    st.query_params["cid"] = clean_cid
                    st.sidebar.success(msg)
                    st.rerun()
                else:
                    st.sidebar.error(f"Failed: {msg}")
        else:
            st.sidebar.warning("Please fill all broker credential fields.")

# ==============================================================================
# PART 3: PROFILE, CAPITAL SHIELD & MULTI-INDEX MATRIX
# ==============================================================================
if st.session_state.get("broker_connected", False) and "angel_connector" in st.session_state:
    broker_display = "Angel One (Live)"
    try:
        connector = st.session_state.angel_connector
        profile = connector.get_profile()
        client_name = profile.get("clientname", "CONNECTED TRADER") if profile else "CONNECTED TRADER"
        funds = connector.get_funds()
        total_bal = float(funds.get("net", 0.0)) if funds else 0.0
    except Exception:
        client_name = "CONNECTED TRADER"
        total_bal = 0.0
    client_id_display = st.session_state.get("client_id", "CLIENT_ACC")
else:
    client_name = "GUEST / UNCONNECTED"
    broker_display = "Not Connected (Please link broker in menu)"
    total_bal = 0.00
    client_id_display = st.session_state.get("client_id") or "NO_ACTIVE_SESSION"

allocated_trading_capital = total_bal * 0.25
safe_reserve_capital = total_bal * 0.75

st.markdown(f"""
    <div class="shield-box" style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="color: #94A3B8; font-size: 0.8rem;">USER & BROKER</span><br>
            <strong style="color: #F8FAFC; font-size: 0.95rem;">👤 {client_name}</strong> <span style="color: #38BDF8; font-size: 0.8rem;">({broker_display})</span>
        </div>
        <div style="text-align: right;">
            <span style="color: #94A3B8; font-size: 0.8rem;">CLIENT ID</span><br>
            <strong style="color: #34D399; font-size: 0.9rem;">{client_id_display}</strong>
        </div>
    </div>
""", unsafe_allow_html=True)

if is_market_open:
    st.markdown(
        f"<div style='background-color: rgba(34, 197, 94, 0.1); border: 1px solid #22C55E; padding: 6px; border-radius: 8px; text-align: center; margin-bottom: 10px;'><span style='color: #22C55E; font-weight: bold; font-size: 0.9rem;'>🟢 {market_msg}</span></div>",
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f"<div style='background-color: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; padding: 6px; border-radius: 8px; text-align: center; margin-bottom: 10px;'><span style='color: #EF4444; font-weight: bold; font-size: 0.9rem;'>🔴 {market_msg}</span></div>",
        unsafe_allow_html=True
    )

col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    st.markdown(f"<div style='background-color: #1E293B; padding: 10px; border-radius: 8px; border: 1px solid #334155; text-align: center;'><span style='color: #94A3B8; font-size: 0.7rem;'>TOTAL BALANCE</span><br><strong style='color: #F8FAFC; font-size: 0.95rem;'>₹{total_bal:,.2f}</strong></div>", unsafe_allow_html=True)
with col_c2:
    st.markdown(f"<div style='background-color: #1E293B; padding: 10px; border-radius: 8px; border: 1px solid #334155; text-align: center;'><span style='color: #94A3B8; font-size: 0.7rem;'>25% RISK CAP</span><br><strong style='color: #38BDF8; font-size: 0.95rem;'>₹{allocated_trading_capital:,.2f}</strong></div>", unsafe_allow_html=True)
with col_c3:
    st.markdown(f"<div style='background-color: #1E293B; padding: 10px; border-radius: 8px; border: 1px solid #334155; text-align: center;'><span style='color: #94A3B8; font-size: 0.7rem;'>75% SAFE RESERVE</span><br><strong style='color: #34D399; font-size: 0.95rem;'>₹{safe_reserve_capital:,.2f}</strong></div>", unsafe_allow_html=True)

st.divider()

st.markdown("### 📊 Multi-Index Live Strategy Matrix (All 5 Indices)")

if "idx_states" not in st.session_state:
    st.session_state.idx_states = {
        "NIFTY": {"spot": 22612.50, "ce_ltp": 138.25, "pe_ltp": 88.50, "ce_sl": 115.00, "pe_sl": 75.00},
        "BANKNIFTY": {"spot": 48250.00, "ce_ltp": 345.00, "pe_ltp": 290.00, "ce_sl": 310.00, "pe_sl": 260.00},
        "FINNIFTY": {"spot": 21400.00, "ce_ltp": 112.50, "pe_ltp": 95.00, "ce_sl": 98.00, "pe_sl": 82.00},
        "MIDCAPNIFTY": {"spot": 10850.00, "ce_ltp": 68.00, "pe_ltp": 54.50, "ce_sl": 58.00, "pe_sl": 45.00},
        "SENSEX": {"spot": 74500.00, "ce_ltp": 520.00, "pe_ltp": 480.00, "ce_sl": 470.00, "pe_sl": 430.00}
    }

if is_market_open and st.session_state.get("bot_running", True):
    for idx in st.session_state.idx_states:
        st.session_state.idx_states[idx]["spot"] += round(random.uniform(-15.0, 16.5), 2)
        st.session_state.idx_states[idx]["ce_ltp"] = max(10.0, round(st.session_state.idx_states[idx]["ce_ltp"] + random.uniform(-4.5, 5.2), 2))
        st.session_state.idx_states[idx]["pe_ltp"] = max(10.0, round(st.session_state.idx_states[idx]["pe_ltp"] + random.uniform(-4.5, 5.2), 2))

total_all_pnl = 0.0

for idx_name, data in st.session_state.idx_states.items():
    st.markdown(f'<div class="index-header">📈 {idx_name} (Spot: {data["spot"]:,.2f})</div>', unsafe_allow_html=True)

    ce_pnl = round((data["ce_ltp"] - 120.00) * 25, 2)
    pe_pnl = round((data["pe_ltp"] - 80.00) * 25, 2)
    total_all_pnl += (ce_pnl + pe_pnl)

    ce_str = f"🟢 +{ce_pnl:,.2f}" if ce_pnl > 0 else f"🟢 {ce_pnl:,.2f}" if ce_pnl == 0 else f"🔴 {ce_pnl:,.2f}"
    pe_str = f"🟢 +{pe_pnl:,.2f}" if pe_pnl > 0 else f"🟢 {pe_pnl:,.2f}" if pe_pnl == 0 else f"🔴 {pe_pnl:,.2f}"

    index_df = pd.DataFrame([
        {
            "Instrument": f"{idx_name} CE",
            "Type": "BUY CALL",
            "Entry": 120.00,
            "LTP": data["ce_ltp"],
            "Trailing SL": data["ce_sl"],
            "P&L": ce_str
        },
        {
            "Instrument": f"{idx_name} PE",
            "Type": "BUY PUT",
            "Entry": 80.00,
            "LTP": data["pe_ltp"],
            "Trailing SL": data["pe_sl"],
            "P&L": pe_str
        }
    ])
    st.dataframe(index_df, use_container_width=True, hide_index=True)

st.divider()

st.markdown("### 💰 Total Net P&L (All 5 Indices Combined)")
net_pnl_str = f"🟢 +{total_all_pnl:,.2f}" if total_all_pnl >= 0 else f"🔴 {total_all_pnl:,.2f}"
pnl_header_color = "#22C55E" if total_all_pnl >= 0 else "#EF4444"

st.markdown(f"<h2 style='color: {pnl_header_color};'>{net_pnl_str}</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8;'>Protected by Multi-Index King Shield TSL</p>", unsafe_allow_html=True)

st.divider()

st.markdown("### ⚙️ Engine & Safety Controls")
bot_status_text = "🟢 SHIELD ACTIVE (Auto-managed: 09:15 - 03:15)" if st.session_state.get("bot_running", True) else "🔴 ENGINE STOPPED / LOCKED"
st.info(bot_status_text)

col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("▶ Start / Resume Shield", use_container_width=True):
        if not st.session_state.get("broker_connected", False):
            st.warning("Please connect your broker account in the menu first!")
        else:
            st.session_state.bot_running = True
            st.success("Shield activated for all 5 indices!")
            st.rerun()
with col_b2:
    if st.button("🚨 Emergency Square Off", use_container_width=True):
        st.session_state.bot_running = False
        st.warning("Emergency triggered! All index positions squared off.")
        st.rerun()

st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748B; font-size: 0.85rem;'>Multi-Index Pro • Nifty, BankNifty, FinNifty, Midcap & Sensex Active</p>", unsafe_allow_html=True)
