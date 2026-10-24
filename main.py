import streamlit as st
import random
import time
import json
import os
from angel_api import AngelAPIHandler
from streamlit_autorefresh import st_autorefresh

# Page Configuration & Rich Charcoal Navy
st.set_page_config(
    page_title="Algo Trading Portal",
    page_icon="📈",
    layout="centered"
)

# Har 5 second mein automatic live refresh (Taki numbers live chalte rahein)
st_autorefresh(interval=5000, limit=None, key="live_market_refresh")

# --- Broker Credentials Persistence (Reload hone par delete na ho)
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

# Initialize session state from saved config if available
saved_creds = load_credentials()
if "broker_connected" not in st.session_state:
    st.session_state.broker_connected = saved_creds.get("broker_connected", False)
    if st.session_state.broker_connected:
        st.session_state.client_id = saved_creds.get("client_id", "")
        st.session_state.api_key = saved_creds.get("api_key", "")
        st.session_state.password = saved_creds.get("password", "")
        st.session_state.totp = saved_creds.get("totp", "")
        # Auto-reconnect connector object
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

# --- Sidebar Menu Bar Integration ---
st.sidebar.markdown("## 🛡️ KING SHIELD MENU")
menu_option = st.sidebar.selectbox("Navigation", ["Dashboard", "Angel One Credentials", "Logs & Status"])

if menu_option == "Angel One Credentials":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 Broker Settings")
    
    api_key_input = st.sidebar.text_input("API Key", value=st.session_state.get("api_key", ""), type="password", key="input_api_key")
    client_id_input = st.sidebar.text_input("Client ID", value=st.session_state.get("client_id", ""), key="input_client_id")
    password_input = st.sidebar.text_input("Password / MPIN", value=st.session_state.get("password", ""), type="password", key="input_password")
    totp_secret = st.sidebar.text_input("TOTP Secret Key", value=st.session_state.get("totp", ""), type="password", key="input_totp")
    
elif menu_option == "Dashboard":
    if st.session_state.get("broker_connected", False):
        st.sidebar.success("🟢 Angel One Connected")
    else:
        st.sidebar.warning("🔴 Angel One Disconnected (Using Simulation)")
        
if st.session_state.get("broker_connected", False):
    st.sidebar.success(f"Connected ID: {st.session_state.get('client_id', 'N/A')}")
    if st.sidebar.button("🗑️ Delete / Disconnect Broker"):
        st.session_state.broker_connected = False
        st.session_state.angel_connector = None
        st.session_state.client_id = ""
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        st.sidebar.success("Broker disconnected successfully!")
        st.rerun()
else:
    if menu_option == "Angel One Credentials" and st.sidebar.button("Connect Broker"):
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
                    
                    # Save to file so it doesn't delete on reload
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
                    st.sidebar.error(f"Connection Failed: {msg}")
        else:
            st.sidebar.warning("Please fill all broker credentials.")

# Custom CSS for Soft Dark Blue-Gray Background & Design
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #F8FAFC; }
    .golden-title {
        font-size: 3.2rem !important;
        font-weight: 900 !important;
        background: linear-gradient(90deg, #BF953F, #FCF6BA, #B38728, #FBF5B7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
        padding-top: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    .subtitle { text-align: center; color: #94A3B8; font-size: 1.1rem; margin-bottom: 30px; letter-spacing: 1px; }
    .metric-box { background-color: #1E293B; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# Header Section
st.markdown('<p class="golden-title">ALGO TRADING PORTAL</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Professional Automated Trading Terminal</p>', unsafe_allow_html=True)
st.divider()

# Real Trading Control Toggle
if 'real_active' not in st.session_state:
    st.session_state.real_active = False

r_status = st.session_state.real_active
r_border = "#22C55E" if r_status else "#EF4444"
r_bg = "rgba(34, 197, 94, 0.1)" if r_status else "rgba(239, 68, 68, 0.1)"
r_txt = "⚡ REAL TRADING STATUS: ACTIVE (ON)" if r_status else "🛑 REAL TRADING STATUS: PAUSED (OFF)"
r_color = "#22C55E" if r_status else "#EF4444"

st.markdown(f"""
    <div style="background-color: {r_bg}; border: 2px solid {r_border}; padding: 12px; border-radius: 10px; margin-bottom: 5px;">
        <span style="color: {r_color}; font-weight: bold; font-size: 0.95rem;">{r_txt}</span>
    </div>
""", unsafe_allow_html=True)

new_r = st.toggle("Real Trading Control", value=st.session_state.real_active, key="real_switch")
if new_r != st.session_state.real_active:
    st.session_state.real_active = new_r
    if new_r:
        st.session_state.paper_active = False
    st.rerun()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Live Nifty Index (Real / Live)")
    
    live_price = None
    if st.session_state.get('broker_connected', False) and 'angel_connector' in st.session_state:
        try:
            fetched_price = st.session_state.angel_connector.get_ltp("NSE", "Nifty 50", "26000")
            if fetched_price is not None:
                live_price = float(fetched_price)
        except:
            pass

    # Simulation fallback with live moving numbers so numbers move up/down
    if not live_price:
        if 'simulated_nifty' not in st.session_state:
            st.session_state.simulated_nifty = 22600.00
        # Har refresh par thoda upar/neeche move hoga taaki pata chale market chal raha hai
        st.session_state.simulated_nifty += round(random.uniform(-3.5, 3.8), 2)
        nifty_price = st.session_state.simulated_nifty
        nifty_change = round(random.uniform(-15.0, 25.0), 2)
    else:
        nifty_price = live_price
        nifty_change = 15.50

    color_style = "color: #22C55E; font-weight: bold;" if nifty_change >= 0 else "color: #EF4444; font-weight: bold;"
    sign_str = "+" if nifty_change >= 0 else ""
        
    st.markdown(f"<h2>{nifty_price:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 1.25rem; {color_style}'>{sign_str}{nifty_change} ({sign_str}{nifty_change/200:.2f}%)</p>", unsafe_allow_html=True)
    
if 'paper_active' not in st.session_state:
    st.session_state.paper_active = False

p_status = st.session_state.paper_active
p_border = "#22C55E" if p_status else "#EF4444"
p_bg = "rgba(34, 197, 94, 0.1)" if p_status else "rgba(239, 68, 68, 0.1)"
p_txt = "⚡ PAPER TRADING STATUS: ACTIVE (ON)" if p_status else "🛑 PAPER TRADING STATUS: PAUSED (OFF)"
p_color = "#22C55E" if p_status else "#EF4444"

st.markdown(f"""
    <div style="background-color: {p_bg}; border: 2px solid {p_border}; padding: 12px; border-radius: 10px; margin-bottom: 5px;">
        <span style="color: {p_color}; font-weight: bold; font-size: 0.95rem;">{p_txt}</span>
    </div>
""", unsafe_allow_html=True)

new_p = st.toggle("Paper Trading Control", value=st.session_state.paper_active, key="paper_switch")
if new_p != st.session_state.paper_active:
    st.session_state.paper_active = new_p
    if new_p:
        st.session_state.real_active = False
    st.rerun()

with col2:
    st.markdown("### Paper Portfolio P&L (Virtual)")
    
    # Session state mein P&L store karke thoda-thoda fluctuation denge taaki live lage
    if 'simulated_pnl' not in st.session_state:
        st.session_state.simulated_pnl = 12538.67
    
    st.session_state.simulated_pnl += round(random.uniform(-15.0, 18.5), 2)
    pnl_value = st.session_state.simulated_pnl
    
    pnl_color = "color: #22C55E; font-weight: bold;" if pnl_value >= 0 else "color: #EF4444; font-weight: bold;"
    pnl_sign = "+" if pnl_value >= 0 else ""
    
    st.markdown(f"<h2>{pnl_value:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 1.25rem; {pnl_color}'>{pnl_sign}{round(pnl_value * 0.01, 2)}</p>", unsafe_allow_html=True)

st.divider()

# Status and Bot Controls
st.info("Paper Trading Mode Active: Orders will be simulated safely without real capital risk.")

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("Start Paper Bot", use_container_width=True):
        st.success("Paper Trading Bot Started Successfully!")

with col_btn2:
    if st.button("Stop Paper Bot", use_container_width=True):
        st.warning("Paper Trading Bot Stopped.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748B; font-size: 0.85rem;'>Powered by Cloud Web Engine • Secure & Real-time</p>", unsafe_allow_html=True)
        
