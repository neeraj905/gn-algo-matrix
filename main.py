import streamlit as st
import streamlit.components.v1 as components
import extra_streamlit_components as stx
import random
import time
import json
from datetime import datetime, time as dtime, timezone, timedelta
from angel_api import AngelAPIHandler
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(
    page_title="Algo Trading Portal - Multi-Index Pro",
    page_icon="🛡️",
    layout="centered"
)

# Live auto-refresh every 5 seconds
st_autorefresh(interval=5000, limit=None, key="multi_index_refresh")

# Cookie Manager (Har user ke mobile browser mein alag-alag data save rakhne ke liye)
cookie_manager = stx.CookieManager(key="algo_user_cookies")

# --- Strict Market Timing & Auto-State Check (09:15 to 15:15 IST) ---
def get_market_status():
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    current_time = ist_now.time()
    current_day = ist_now.weekday()

    if current_day >= 5:
        return False, "Market Closed (Weekend)", ist_now

    m_start = dtime(9, 15)
    m_end = dtime(15, 15)

    if m_start <= current_time <= m_end:
        return True, "Market Open (Active Trading Window)", ist_now
    elif current_time < m_start:
        return False, "Pre-Market (Waiting for 09:15 AM)", ist_now
    else:
        return False, "Market Closed (Post 03:15 PM - Locked)", ist_now

is_market_open, market_msg, ist_now = get_market_status()

# --- Session State Initialization ---
defaults = {
    "broker_connected": False,
    "client_id": "",
    "api_key": "",
    "password": "",
    "totp": "",
    "angel_connector": None,
    "bot_running": False,
    "danger_alarm": False,
    "danger_reason": "",
    "trading_mode": "PAPER (Safe Test)",
    "max_loss_limit": -5000.0,
    "logs": []
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def add_log(msg):
    ts = ist_now.strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{ts}] {msg}")
    st.session_state.logs = st.session_state.logs[:50]

# --- Auto-Restore User Credentials from Mobile Browser Cookie on Refresh ---
saved_creds = cookie_manager.get("angel_user_creds")
if saved_creds and not st.session_state.broker_connected:
    try:
        creds = json.loads(saved_creds) if isinstance(saved_creds, str) else saved_creds
        if creds.get("client_id") and creds.get("api_key"):
            connector = AngelAPIHandler(
                creds["api_key"], creds["client_id"], creds["password"], creds["totp"]
            )
            success, msg = connector.connect()
            if success:
                st.session_state.broker_connected = True
                st.session_state.angel_connector = connector
                st.session_state.client_id = creds["client_id"]
                st.session_state.api_key = creds["api_key"]
                st.session_state.password = creds["password"]
                st.session_state.totp = creds["totp"]
                add_log(f"Auto-reconnected Client: {creds['client_id']}")
    except Exception as e:
        add_log(f"Auto-reconnect skipped: {e}")

# --- Audio + Visual Danger Alarm Function (Khatre Ki Batti & Siren) ---
def trigger_danger_alarm(reason):
    st.session_state.danger_alarm = True
    st.session_state.danger_reason = reason
    # Web Audio API Siren Sound (Mobile browser par bina external mp3 ke bajega)
    components.html("""
        <script>
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(880, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.5);
            gain.gain.setValueAtTime(0.3, ctx.currentTime);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.8);
        } catch(e) {}
        </script>
    """, height=0)

# --- Emergency Square-Off & Kill Switch Function ---
def execute_emergency_square_off(reason="Manual Emergency Triggered"):
    st.session_state.bot_running = False
    trigger_danger_alarm(reason)
    add_log(f"🚨 EMERGENCY SQUARE-OFF: {reason}")
    
    if st.session_state.broker_connected and st.session_state.angel_connector:
        if st.session_state.trading_mode == "LIVE REAL MONEY":
            try:
                # Real broker open orders cancel & positions exit call
                if hasattr(st.session_state.angel_connector, "square_off_all"):
                    st.session_state.angel_connector.square_off_all()
                    add_log("✅ All REAL open orders cancelled & positions squared off!")
                else:
                    add_log("⚠️ Add 'square_off_all()' method in angel_api.py for live exit.")
            except Exception as e:
                add_log(f"❌ Square-off API Error: {e}")
        else:
            add_log("✅ Paper Trading positions squared off safely.")

# --- Auto 3:15 PM Square-Off Check ---
if ist_now.time() >= dtime(15, 15) and st.session_state.bot_running:
    execute_emergency_square_off("03:15 PM Auto Market Close Square-Off")

# --- Sidebar Navigation & Per-User Broker Settings ---
st.sidebar.markdown("## 🛡️ MULTI-INDEX PRO MENU")
menu_option = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard & Index Matrix", "Broker Account Settings", "Execution Logs"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Safety & Mode Settings")
st.session_state.trading_mode = st.sidebar.radio(
    "Trading Mode",
    ["PAPER (Safe Test)", "LIVE REAL MONEY"],
    index=0 if st.session_state.trading_mode == "PAPER (Safe Test)" else 1
)
st.session_state.max_loss_limit = st.sidebar.number_input(
    "Max Daily Loss Alarm Limit (₹)",
    value=float(st.session_state.max_loss_limit),
    step=500.0
)

if menu_option == "Broker Account Settings":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 Connect Your Demat Broker")
    st.sidebar.caption("Aapka data sirf aapke mobile browser mein save rahega.")
    api_key_input = st.sidebar.text_input("API Key", value=st.session_state.api_key, type="password")
    client_id_input = st.sidebar.text_input("Client ID", value=st.session_state.client_id)
    password_input = st.sidebar.text_input("Password / MPIN", value=st.session_state.password, type="password")
    totp_secret = st.sidebar.text_input("TOTP Secret Key", value=st.session_state.totp, type="password")

    if st.sidebar.button("💾 Save & Connect Broker"):
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
                    
                    # Save in user's own browser cookie for 7 days (Refresh-Proof)
                    creds_payload = json.dumps({
                        "api_key": api_key_input,
                        "client_id": client_id_input,
                        "password": password_input,
                        "totp": totp_secret
                    })
                    cookie_manager.set("angel_user_creds", creds_payload, expires_at=datetime.now() + timedelta(days=7))
                    add_log(f"Connected & Saved Client: {client_id_input}")
                    st.sidebar.success("Connected & Saved! Refresh karne par bhi data nahi jayega.")
                    st.rerun()
                else:
                    st.sidebar.error(f"Failed: {msg}")
        else:
            st.sidebar.warning("Please fill all 4 broker fields.")

if st.session_state.broker_connected:
    st.sidebar.success(f"🟢 Connected: {st.session_state.client_id}")
    if st.sidebar.button("🗑️ Disconnect & Clear Data"):
        cookie_manager.delete("angel_user_creds")
        st.session_state.broker_connected = False
        st.session_state.angel_connector = None
        st.session_state.client_id = ""
        st.session_state.api_key = ""
        st.session_state.password = ""
        st.session_state.totp = ""
        st.rerun()

# --- Custom CSS (Dark Theme + Blinking Red Danger Light) ---
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #F8FAFC; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .golden-title {
        font-size: 2.2rem !important;
        font-weight: 900 !important;
        background: linear-gradient(90deg, #BF953F, #FCF6BA, #B38728, #FBF5B7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
    }
    .subtitle { text-align: center; color: #94A3B8; font-size: 0.9rem; margin-bottom: 15px; }
    .shield-box { background-color: #1E293B; border: 1px solid #334155; padding: 14px; border-radius: 10px; margin-bottom: 12px; }
    @keyframes blinker {
        50% { opacity: 0.2; background-color: #7F1D1D; }
    }
    .danger-beacon {
        background-color: #DC2626;
        color: #FFFFFF;
        padding: 16px;
        border-radius: 10px;
        border: 3px solid #FCA5A5;
        text-align: center;
        font-weight: 900;
        font-size: 1.1rem;
        animation: blinker 1s linear infinite;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
