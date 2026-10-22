import streamlit as st
import random
import time
from angel_api import AngelAPIHandler

from streamlit_autorefresh import st_autorefresh

# Page Configuration & Rich Charcoal Navy
st.set_page_config(
    page_title="Algo Trading Portal",
    page_icon="📈",
    layout="centered"
)

# Har 5 second mein automatic live refresh ke liye
st_autorefresh(interval=5000, limit=None, key="live_market_refresh")

# --- Sidebar Menu Bar Integration ---
st.sidebar.markdown("## 🛡️ KING SHIELD MENU")
menu_option = st.sidebar.selectbox("Navigation", ["Dashboard", "Angel One Credentials", "Logs & Status"])

if menu_option == "Angel One Credentials":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 Broker Settings")
    
    api_key_input = st.sidebar.text_input("API Key", type="password")
    client_id_input = st.sidebar.text_input("Client ID")
    password_input = st.sidebar.text_input("Password / MPIN", type="password")
    totp_secret = st.sidebar.text_input("TOTP Secret Key", type="password")
    
        if st.session_state.get("broker_connected", False):
        st.sidebar.success(f"Connected ID: {st.session_state.get('client_id', 'N/A')}")
        if st.sidebar.button("🗑️ Delete / Disconnect Broker"):
            st.session_state.broker_connected = False
            st.session_state.angel_connector = None
            st.session_state.client_id = ""
            st.sidebar.success("Broker disconnected successfully!")
            st.rerun()
    else:
        if st.sidebar.button("Connect Broker"):
            if api_key_input and client_id_input and password_input and totp_secret:
                with st.spinner("Connecting to Angel One..."):
                    from angel_api import AngelAPIHandler
                    connector = AngelAPIHandler(api_key_input, client_id_input, password_input, totp_secret)
                    success, msg = connector.connect()
                    if success:
                        st.session_state.broker_connected = True
                        st.session_state.angel_connector = connector
                        st.session_state.client_id = client_id_input
                        st.sidebar.success(msg)
                        st.rerun()
                    else:
                        st.sidebar.error(f"Connection Failed: {msg}")
            else:
                st.sidebar.warning("Please fill all broker credentials.")

elif menu_option == "Dashboard":
    if 'is_connected' in st.session_state and st.session_state.is_connected:
        st.sidebar.success("🟢 Angel One Connected")
    else:
        st.sidebar.warning("🔴 Angel One Disconnected (Using Simulation)")


# Custom CSS for Soft Dark Blue-Gray Background, 4x Bold Golden Title, and Trading Colors
st.markdown("""
    <style>
    /* Main Background: Soft Dark Blue-Gray / Rich Charcoal Navy */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    
    /* 4x Larger, Bold, Glowing Golden Title */
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
    
    .subtitle {
        text-align: center;
        color: #94A3B8;
        font-size: 1.1rem;
        margin-bottom: 30px;
        letter-spacing: 1px;
    }
    
    /* Trading Card Styling */
    .metric-box {
        background-color: #1E293B;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Header Section with 4x Larger Golden Title
st.markdown('<p class="golden-title">ALGO TRADING PORTAL</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Professional Automated Trading Terminal</p>', unsafe_allow_html=True)

st.divider()

# Live Market Data (Angel One Live Integration or Simulation Fallback)
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
        st.session_state.paper_active = False  # Paper automatic off
    st.rerun()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Live Nifty Index")
    
        # Fetch Live Nifty Price from Angel One
    live_price = None
    if st.session_state.get('broker_connected', False) and 'angel_connector' in st.session_state:
        try:
            fetched_price = st.session_state.angel_connector.get_ltp("NSE", "Nifty 50", "26000")
            if fetched_price is not None:
                live_price = float(fetched_price)
        except Exception as e:
            pass

    # Fallback to simulation if live price is not reachable
    if not live_price:
        if 'simulated_nifty' not in st.session_state:
            st.session_state.simulated_nifty = 22726.15
        live_price = st.session_state.simulated_nifty
    else:
        st.session_state.simulated_nifty = live_price

    if live_price:
        nifty_price = live_price
        nifty_change = 15.50
    else:
        nifty_price = 24350.25
        nifty_change = 1.25
        
        

    if live_price:
        nifty_price = live_price
        nifty_change = 15.50
    else:
        nifty_price = 24350.25 + round(random.uniform(-5.0, 5.0), 2)
        nifty_change = round(random.uniform(-20.0, 35.0), 2)

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
    st.markdown("### Paper Portfolio P&L")
    pnl_value = 12450.00 + round(random.uniform(-100.0, 150.0), 2)
    pnl_color = "color: #22C55E; font-weight: bold;" if pnl_value >= 0 else "color: #EF4444; font-weight: bold;"
    pnl_sign = "+" if pnl_value >= 0 else ""
    
    st.markdown(f"<h2>{pnl_value:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 1.25rem; {pnl_color}'>{pnl_sign}{pnl_value * 0.01:.2f}</p>", unsafe_allow_html=True)

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
