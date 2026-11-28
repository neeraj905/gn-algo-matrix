import streamlit as st
import streamlit.components.v1 as components
import base64
import json
from datetime import datetime, time as dtime, timezone, timedelta
from broker_manager import MultiBrokerHandler
from market_engine import MultiIndexLiveEngine, INDEX_CONFIG
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Algo Trading Portal - Institutional Shield", page_icon="🛡️", layout="centered")
st_autorefresh(interval=1000, limit=None, key="live_1sec_scanner_refresh")

def get_market_status():
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    current_time = ist_now.time()
    if ist_now.weekday() >= 5:
        return False, "Market Closed (Weekend)", ist_now
    if dtime(9, 15) <= current_time <= dtime(15, 15):
        return True, "Market Open (Active 1-Sec Scanner)", ist_now
    elif current_time < dtime(9, 15):
        return False, "Pre-Market (Waiting for 09:15 AM)", ist_now
    return False, "Market Closed (Post 03:15 PM - Locked)", ist_now

is_market_open, market_msg, ist_now = get_market_status()

defaults = {"broker_connected": False, "selected_broker": "Angel One", "creds": {}, "broker_handler": None, "market_engine": MultiIndexLiveEngine(), "bot_running": False, "capital_locked": False, "lock_reason": "", "danger_alarm": False, "danger_reason": "", "trading_mode": "PAPER (Safe Test)", "max_loss_limit": -1000.0, "lots_per_index": 1, "active_trades": {}, "prev_spots": {}, "realized_pnl": 0.0, "scan_count": 0, "logs": []}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.session_state.scan_count += 1

def add_log(msg):
    ts = ist_now.strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{ts}] {msg}")
    st.session_state.logs = st.session_state.logs[:100]

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

def trigger_danger_alarm(reason):
    st.session_state.danger_alarm = True
    st.session_state.danger_reason = reason
    components.html("<script>try{const c=new(window.AudioContext||window.webkitAudioContext)();const o=c.createOscillator();const g=c.createGain();o.type='sawtooth';o.frequency.setValueAtTime(980,c.currentTime);o.frequency.exponentialRampToValueAtTime(420,c.currentTime+0.6);g.gain.setValueAtTime(0.4,c.currentTime);o.connect(g);g.connect(c.destination);o.start();o.stop(c.currentTime+0.9);}catch(e){}</script>", height=0)

def trigger_capital_lock(reason):
    st.session_state.bot_running = False
    st.session_state.capital_locked = True
    st.session_state.lock_reason = reason
    trigger_danger_alarm(f"CAPITAL LOCKED: {reason}")
    add_log(f"🔒 AUTO CAPITAL LOCK: {reason}")

def execute_emergency_square_off(reason="Emergency Button Pressed"):
    st.session_state.bot_running = False
    st.session_state.capital_locked = True
    st.session_state.lock_reason = reason
    st.session_state.active_trades = {}
    trigger_danger_alarm(reason)
    add_log(f"🚨 EMERGENCY EXIT ALL: {reason}")
    if st.session_state.broker_connected and st.session_state.broker_handler:
        if st.session_state.trading_mode == "LIVE REAL MONEY":
            ok, res_logs = st.session_state.broker_handler.square_off_all()
            for item in res_logs:
                add_log(f"Broker Exit: {item}")
        else:
            add_log("✅ Paper Trading positions closed safely.")

if ist_now.time() >= dtime(15, 15) and st.session_state.bot_running:
    execute_emergency_square_off("03:15 PM Auto Market Close Square-Off")

css_code = "<style>.stApp{background-color:#0F172A;color:#F8FAFC;}header[data-testid='stHeader'],[data-testid='stToolbar'],[data-testid='stDecoration'],.stDeployButton,#GithubIcon,footer{display:none!important;}.golden-title{font-size:2.1rem!important;font-weight:900!important;background:linear-gradient(90deg,#BF953F,#FCF6BA,#B38728,#FBF5B7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin-bottom:0px;}.subtitle{text-align:center;color:#94A3B8;font-size:0.88rem;margin-bottom:12px;}.shield-box{background-color:#1E293B;border:1px solid #334155;padding:12px;border-radius:10px;margin-bottom:10px;}@keyframes blinker{50%{opacity:0.2;background-color:#7F1D1D;}}.danger-beacon{background-color:#DC2626;color:#FFFFFF;padding:16px;border-radius:10px;border:3px solid #FCA5A5;text-align:center;font-weight:900;font-size:1.1rem;animation:blinker 0.8s linear infinite;margin-bottom:12px;}.safe-beacon{background-color:#065F46;color:#ECFDF5;padding:14px;border-radius:10px;border:2px solid #34D399;text-align:center;font-weight:800;font-size:1rem;margin-bottom:12px;}.lock-beacon{background-color:#7C2D12;color:#FFEDD5;padding:14px;border-radius:10px;border:2px solid #FB923C;text-align:center;font-weight:800;font-size:1rem;margin-bottom:12px;}[data-testid='stExpander']{background-color:#1E293B!important;border:1px solid #334155!important;border-radius:10px!important;}[data-testid='stExpander'] summary,[data-testid='stExpander'] p,td,th,label,[data-testid='stRadio'] p{color:#F8FAFC!important;font-weight:600!important;}[data-testid='stMetricValue']{color:#38BDF8!important;}[data-testid='stMetricLabel'] p{color:#94A3B8!important;}button[kind='secondary']{background-color:#1E293B!important;color:#F8FAFC!important;border:1px solid #475569!important;}</style>"
st.markdown(css_code, unsafe_allow_html=True)

st.markdown('<div class="golden-title">ALGO TRADING PORTAL</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">1-Sec Live Scanner #{st.session_state.scan_count} • 5% Trailing Profit & Capital Lock Shield</div>', unsafe_allow_html=True)

menu_option = st.radio("Navigation", ["📊 Live Dashboard", "🔑 Broker Account Settings", "📜 Execution Logs"], horizontal=True, label_visibility="collapsed")
st.ma
rkdown("---")
