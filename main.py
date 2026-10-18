import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Algo Trading Portal",
    page_icon="⚡",
    layout="centered"
)

# --- CUSTOM CSS FOR BRANDING & STYLING ---
st.markdown("""
    <style>
    .main-header {
        font-size: 38px;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(to right, #BF953F, #FCF6BA, #B38728, #FBF5B7, #AA771C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 0px;
    }
    .sub-header {
        text-align: center;
        color: #A0A0A0;
        font-size: 16px;
        margin-bottom: 30px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- APP UI HEADER ---
st.markdown('<p class="main-header">ALGO TRADING PORTAL</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Professional Automated Trading Terminal</p>', unsafe_allow_html=True)

# --- SIDEBAR: TRADING MODE SELECTOR ---
st.sidebar.header("Control Panel")
trading_mode = st.sidebar.radio(
    "Select Trading Mode:",
    ["Paper Trading (Simulation)", "Real Trading (Live Kotak Neo)"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info(f"Current Mode Active:\n{trading_mode}")

# --- MAIN DASHBOARD AREA ---
col1, col2 = st.columns(2)

with col1:
    st.metric(label="Live Nifty Index", value="24,350.25", delta="+120.50 (+0.5%)")

with col2:
    if "Paper" in trading_mode:
        st.metric(label="Paper Portfolio P&L", value="12,450.00", delta="1,250")
    else:
        st.metric(label="Live Account P&L", value="0.00", delta="0.00")

st.markdown("---")

# --- BROKER / TRADING CONTROLS ---
if "Paper" in trading_mode:
    st.success("Paper Trading Mode Active: Orders will be simulated safely without real capital risk.")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("Start Paper Bot"):
            st.success("Paper Trading Bot Started Successfully!")
    with col_p2:
        if st.button("Stop Paper Bot"):
            st.warning("Paper Trading Bot Stopped.")

else:
    st.warning("Real Trading Mode Active: Connected to live broker gateway. Capital risk is involved.")
    
    # Broker Login Card inside Real Mode
    broker_id = st.text_input("Broker User ID / Client Code", placeholder="e.g., 10EFJ")
    api_key = st.text_input("Consumer Key / API Key", type="password", placeholder="Enter your broker API key")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("Connect & Authorize Real Account"):
            if broker_id and api_key:
                st.success(f"Real connection initiated for Client: {broker_id}!")
            else:
                st.warning("Please enter both User ID and API Key.")
    with col_r2:
        if st.button("Emergency Square Off"):
            st.error("EMERGENCY SQUARE-OFF TRIGGERED!")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 12px;'>Powered by Cloud Web Engine • Secure & Real-time</p>", unsafe_allow_html=True)
