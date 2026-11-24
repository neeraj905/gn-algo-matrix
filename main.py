import streamlit as st
import streamlit.components.v1 as components
import base64
import json
from datetime import datetime, time as dtime, timezone, timedelta
from broker_manager import MultiBrokerHandler
from market_engine import MultiIndexLiveEngine, INDEX_CONFIG
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Algo Trading Portal - Multi-Broker Pro",
    page_icon="🛡️",
    layout="centered"
)

# Har 8 second mein safe refresh (taaki live data load hone ka poora samay mile)
st_autorefresh(interval=8000, limit=None, key="multi_index_live_refresh")

# --- Market Timing Check (09:15 to 15:15 IST) ---
def get_market_status():
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    current_time = ist_now.time()
    if ist_now.weekday() >= 5:
        return False, "Market Closed (Weekend)", ist_now
    if dtime(9, 15) <= current_time <= dtime(15, 15):
        return True, "Market Open (Active Trading Window)", ist_now
    elif current_time < dtime(9, 15):
        return False, "Pre-Market (Waiting for 09:15 AM)", ist_now
    return False, "Market Closed (Post 03:15 PM - Locked)", ist_now

is_market_open, market_msg, ist_now = get_market_status()

# --- Session State Setup ---
defaults = {
    "broker_connected": False,
    "selected_broker": "Angel One",
    "creds": {},
    "broker_handler": None,
    "market_engine": MultiIndexLiveEngine(),
    "bot_running": False,
    "danger_alarm": False,
    "danger_reason": "",
    "trading_mode": "PAPER (Safe Test)",
    "max_loss_limit": -5000.0,
    "lots_per_index": 1,
    "active_trades": {},
    "realized_pnl": 0.0,
    "logs": []
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def add_log(msg):
    ts = ist_now.strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{ts}] {msg}")
    st.session_state.logs = st.session_state.logs[:80]

# --- Refresh-Proof Per-User Persistence via URL Session Token ---
if not st.session_state.broker_connected and "session" in st.query_params:
    try:
        raw_b64 = st.query_params["session"]
        decoded = json.loads(base64.urlsafe_b64decode(raw_b64.encode()).decode())
        b_name = decoded.get("broker_name")
        b_creds = decoded.get("creds", {})
        if b_name and b_creds:
            handler = MultiBrokerHandler(b_name, b_creds)
            ok, msg = handler.connect()
            if ok:
                st.session_state.broker_connected = True
                st.session_state.selected_broker = b_name
                st.session_state.creds = b_creds
                st.session_state.broker_handler = handler
                add_log(f"Auto-restored {b_name} ({b_creds.get('client_id', '')})")
    except Exception as e:
        add_log(f"Auto-restore skipped: {e}")

# --- Khatre Ki Batti + Siren Alarm ---
def trigger_danger_alarm(reason):
    st.session_state.danger_alarm = True
    st.session_state.danger_reason = reason
    components.html("""
        <script>
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(920, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(420, ctx.currentTime + 0.6);
            gain.gain.setValueAtTime(0.35, ctx.currentTime);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.9);
        } catch(e) {}
        </script>
    """, height=0)

def execute_emergency_square_off(reason="Emergency Button Pressed"):
    st.session_state.bot_running = False
    st.session_state.active_trades = {}
    trigger_danger_alarm(reason)
    add_log(f"🚨 EMERGENCY SQUARE-OFF: {reason}")
    if st.session_state.broker_connected and st.session_state.broker_handler:
        if st.session_state.trading_mode == "LIVE REAL MONEY":
            ok, res_logs = st.session_state.broker_handler.square_off_all()
            for item in res_logs:
                add_log(f"Broker Exit: {item}")
        else:
            add_log("✅ Paper Trading positions closed safely.")

if ist_now.time() >= dtime(15, 15) and st.session_state.bot_running:
    execute_emergency_square_off("03:15 PM Auto Market Close Square-Off")

# --- Sidebar: Multi-Broker Account & Risk Settings ---
st.sidebar.markdown("## 🛡️ MULTI-BROKER PRO MENU")
menu_option = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard & Index Matrix", "Broker Account Settings", "Execution Logs"]
)

st.sidebar.markdown("---")
st.session_state.trading_mode = st.sidebar.radio(
    "Trading Mode",
    ["PAPER (Safe Test)", "LIVE REAL MONEY"],
    index=0 if st.session_state.trading_mode == "PAPER (Safe Test)" else 1
)
st.session_state.lots_per_index = st.sidebar.number_input("Lots Per Index", min_value=1, max_value=20, value=int(st.session_state.lots_per_index))
st.session_state.max_loss_limit = st.sidebar.number_input("Max Daily Loss Alarm Limit (₹)", value=float(st.session_state.max_loss_limit), step=500.0)

if menu_option == "Broker Account Settings":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 Select & Connect Your Broker")
    brokers_list = ["Angel One", "Kotak Neo", "Dhan", "Zerodha Kite", "Upstox"]
    default_idx = brokers_list.index(st.session_state.selected_broker) if st.session_state.selected_broker in brokers_list else 0
    chosen_broker = st.sidebar.selectbox("Apna Broker Chunein", brokers_list, index=default_idx)
    
    prev = st.session_state.creds
    new_creds = {}

    if chosen_broker == "Angel One":
        new_creds["client_id"] = st.sidebar.text_input("Angel Client ID", value=prev.get("client_id", ""))
        new_creds["api_key"] = st.sidebar.text_input("SmartAPI Key", value=prev.get("api_key", ""), type="password")
        new_creds["password"] = st.sidebar.text_input("MPIN / Password", value=prev.get("password", ""), type="password")
        new_creds["totp_secret"] = st.sidebar.text_input("TOTP Secret Key", value=prev.get("totp_secret", ""), type="password")

    elif chosen_broker == "Kotak Neo":
        new_creds["client_id"] = st.sidebar.text_input("Kotak UCC (Client ID)", value=prev.get("client_id", ""))
        new_creds["mobile_number"] = st.sidebar.text_input("Registered Mobile (+91...)", value=prev.get("mobile_number", ""))
        new_creds["access_token"] = st.sidebar.text_input("Neo Access Token", value=prev.get("access_token", ""), type="password")
        new_creds["password"] = st.sidebar.text_input("MPIN", value=prev.get("password", ""), type="password")
        new_creds["totp_secret"] = st.sidebar.text_input("TOTP Secret Key", value=prev.get("totp_secret", ""), type="password")

    elif chosen_broker == "Dhan":
        new_creds["client_id"] = st.sidebar.text_input("Dhan Client ID", value=prev.get("client_id", ""))
        new_creds["access_token"] = st.sidebar.text_input("Dhan Access Token", value=prev.get("access_token", ""), type="password")

    elif chosen_broker in ["Zerodha Kite", "Upstox"]:
        new_creds["client_id"] = st.sidebar.text_input(f"{chosen_broker} User ID", value=prev.get("client_id", ""))
        new_creds["api_key"] = st.sidebar.text_input("API Key", value=prev.get("api_key", ""), type="password")
        new_creds["access_token"] = st.sidebar.text_input("Daily Access Token", value=prev.get("access_token", ""), type="password")

    if st.sidebar.button("💾 Save & Connect Broker"):
        if all(str(v).strip() for v in new_creds.values()):
            with st.spinner(f"Connecting to {chosen_broker}..."):
                handler = MultiBrokerHandler(chosen_broker, new_creds)
                ok, msg = handler.connect()
                if ok:
                    st.session_state.broker_connected = True
                    st.session_state.selected_broker = chosen_broker
                    st.session_state.creds = new_creds
                    st.session_state.broker_handler = handler
                    
                    payload = json.dumps({"broker_name": chosen_broker, "creds": new_creds})
                    b64_token = base64.urlsafe_b64encode(payload.encode()).decode()
                    st.query_params["session"] = b64_token
                    
                    add_log(f"Connected {chosen_broker}: {new_creds.get('client_id')}")
                    st.sidebar.success(f"{msg} (Saved! Refresh par bhi data rahega)")
                    st.rerun()
                else:
                    st.sidebar.error(f"Failed: {msg}")
        else:
            st.sidebar.warning("Kripya saari fields bharein.")

if st.session_state.broker_connected:
    st.sidebar.success(f"🟢 {st.session_state.selected_broker}: {st.session_state.creds.get('client_id')}")
    if st.sidebar.button("🗑️ Disconnect & Clear Account"):
        st.query_params.clear()
        st.session_state.broker_connected = False
        st.session_state.creds = {}
        st.session_state.broker_handler = None
        st.rerun()

# --- Custom CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #F8FAFC; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .golden-title {
        font-size: 2.2rem !important; font-weight: 900 !important;
        background: linear-gradient(90deg, #BF953F, #FCF6BA, #B38728, #FBF5B7);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 0px;
    }
    .subtitle { text-align: center; color: #94A3B8; font-size: 0.9rem; margin-bottom: 15px; }
    .shield-box { background-color: #1E293B; border: 1px solid #334155; padding: 14px; border-radius: 10px; margin-bottom: 12px; }
    @keyframes blinker { 50% { opacity: 0.2; background-color: #7F1D1D; } }
    .danger-beacon {
