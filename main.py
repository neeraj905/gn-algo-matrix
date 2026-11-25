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
        background-color: #DC2626; color: #FFFFFF; padding: 16px; border-radius: 10px;
        border: 3px solid #FCA5A5; text-align: center; font-weight: 900; font-size: 1.1rem;
        animation: blinker 1s linear infinite; margin-bottom: 15px;
    }
        [data-testid="stExpander"] { background-color: #1E293B !important; border: 1px solid #334155 !important; border-radius: 10px !important; }
    [data-testid="stExpander"] summary, [data-testid="stExpander"] p, td, th { color: #F8FAFC !important; }
    [data-testid="stMetricValue"] { color: #38BDF8 !important; }
    button[kind="secondary"] { background-color: #1E293B !important; color: #F8FAFC !important; border: 1px solid #475569 !important; }
    
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown('<div class="golden-title">ALGO TRADING PORTAL</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Multi-Broker & Multi-Index Pro • Nifty, BankNifty, FinNifty, Midcap & Sensex Shield</div>', unsafe_allow_html=True)

# --- Blinking Red Danger Light ---
if st.session_state.danger_alarm:
    st.markdown(f"""
        <div class="danger-beacon">
            🚨 KHATRE KI GHANTI / DANGER ALERT 🚨<br>
            <span style="font-size: 0.9rem; font-weight: normal;">{st.session_state.danger_reason}</span>
        </div>
    """, unsafe_allow_html=True)
    if st.button("🔕 Alarm Band Karein (Reset Alert)"):
        st.session_state.danger_alarm = False
        st.session_state.danger_reason = ""
        st.rerun()

# --- User & Broker Card ---
if st.session_state.broker_connected:
    user_title = f"{st.session_state.selected_broker.upper()} • {st.session_state.creds.get('client_id', '')}"
    user_sub = f"Active Mode: {st.session_state.trading_mode} (Device Isolated)"
else:
    user_title = "GUEST / UNCONNECTED"
    user_sub = "Sidebar (>>) mein 'Broker Account Settings' khol kar apna broker jodein"

st.markdown(f"""
    <div class="shield-box">
        <div style="font-size: 0.75rem; color: #94A3B8;">ACTIVE USER & BROKER</div>
        <div style="font-size: 1.1rem; font-weight: bold; color: #F8FAFC;">👤 {user_title}</div>
        <div style="font-size: 0.85rem; color: #38BDF8;">{user_sub}</div>
    </div>
""", unsafe_allow_html=True)

if is_market_open:
    st.success(f"🟢 {market_msg}")
else:
    st.warning(f"🟠 {market_msg}")

# --- Balance & 25%/75% Shield ---
total_balance = st.session_state.broker_handler.get_balance() if st.session_state.broker_connected else 100000.0
risk_cap = total_balance * 0.25
safe_reserve = total_balance * 0.75

col1, col2, col3 = st.columns(3)
col1.metric("TOTAL BALANCE", f"₹{total_balance:,.2f}")
col2.metric("25% RISK CAP", f"₹{risk_cap:,.2f}")
col3.metric("75% SAFE RESERVE", f"₹{safe_reserve:,.2f}")

# --- Main Content ---
if menu_option == "Execution Logs":
    st.subheader("📜 Live Execution & Safety Logs")
    for log in st.session_state.logs or ["Abhi koi log nahi hai."]:
        st.text(log)
else:
    st.subheader("📊 Multi-Index Live Strategy Matrix (All 5 Indices)")
    engine = st.session_state.market_engine
    handler = st.session_state.broker_handler
    
    unrealized_pnl = 0.0
    sideways_count = 0

    for idx_name in INDEX_CONFIG.keys():
        spot, chg_pct = engine.get_live_spot_and_change(idx_name, handler)
        signal = engine.evaluate_signal(chg_pct)
        if signal == "SIDEWAYS":
            sideways_count += 1

        ce_contract, pe_contract = engine.get_atm_option_contracts(idx_name, spot) if spot else (None, None)
        ce_sym = ce_contract["symbol"] if ce_contract else f"{idx_name} ATM CE"
        pe_sym = pe_contract["symbol"] if pe_contract else f"{idx_name} ATM PE"

        ce_ltp = None
        pe_ltp = None
        if handler and hasattr(handler, "get_ltp"):
            if ce_contract:
                ce_ltp = handler.get_ltp(ce_contract["exchange"], ce_sym, ce_contract["token"])
            if pe_contract:
                pe_ltp = handler.get_ltp(pe_contract["exchange"], pe_sym, pe_contract["token"])

        active = st.session_state.active_trades.get(idx_name)
        idx_pnl = 0.0

        if active:
            curr_ltp = ce_ltp if active["side"] == "CE" else pe_ltp
            if curr_ltp:
                idx_pnl = round((curr_ltp - active["entry"]) * active["qty"], 2)
                new_sl = round(curr_ltp * 0.88, 2)
                if new_sl > active["sl"]:
                    active["sl"] = new_sl

                if curr_ltp <= active["sl"] or curr_ltp >= active["target"]:
                    if st.session_state.trading_mode == "LIVE REAL MONEY" and handler:
                        exit_px = max(0.05, curr_ltp * 0.98)
                        handler.place_limit_order(active["symbol"], active["token"], "SELL", active["qty"], exit_px, active["exchange"])
                    st.session_state.realized_pnl += idx_pnl
                    add_log(f"EXIT {active['symbol']} @ ₹{curr_ltp} | P&L: ₹{idx_pnl}")
                    del st.session_state.active_trades[idx_name]
                    active = None

        if not active and st.session_state.bot_running and is_market_open and signal in ["BUY_CE", "BUY_PE"]:
            chosen = ce_contract if signal == "BUY_CE" else pe_contract
            entry_ltp = ce_ltp if signal == "BUY_CE" else pe_ltp
            if chosen and entry_ltp and entry_ltp > 5.0:
                qty = chosen["lot_size"] * int(st.session_state.lots_per_index)
                trade_cost = entry_ltp * qty
                if trade_cost <= risk_cap:
                    order_ok = True
                    if st.session_state.trading_mode == "LIVE REAL MONEY" and handler:
                        buy_px = round(entry_ltp * 1.01, 2)
                        order_ok, oid = handler.place_limit_order(chosen["symbol"], chosen["token"], "BUY", qty, buy_px, chosen["exchange"])
                        add_log(f"LIVE BUY {chosen['symbol']} ({qty}) -> {oid}")
                    else:
                        add_log(f"PAPER BUY {chosen['symbol']} ({qty}) @ ₹{entry_ltp}")

                    if order_ok:
                        st.session_state.active_trades[idx_name] = {
                            "symbol": chosen["symbol"],
                            "token": chosen["token"],
                            "exchange": chosen["exchange"],
                            "side": "CE" if signal == "BUY_CE" else "PE",
                            "entry": entry_ltp,
                            "qty": qty,
                            "sl": round(entry_ltp * 0.85, 2),
                            "target": round(entry_ltp * 1.30, 2)
                        }

        unrealized_pnl += idx_pnl
        spot_str = f"{spot:,.2f} ({chg_pct:+.2f}%)" if spot else "Fetching..."
        status_badge = "🟡 SIDEWAYS" if signal == "SIDEWAYS" else ("🟢 BULLISH" if signal == "BUY_CE" else "🔴 BEARISH")

        with st.expander(f"📈 {idx_name} | Spot: {spot_str} | {status_badge}", expanded=True):
            st.table([
                {
                    "Contract": ce_sym,
                    "Signal": "ACTIVE BUY" if (active and active["side"] == "CE") else "WAIT",
                    "Entry": active["entry"] if (active and active["side"] == "CE") else "-",
                    "Live LTP": ce_ltp if ce_ltp else "API Req",
                    "Trailing SL": active["sl"] if (active and active["side"] == "CE") else "-"
                },
                {
                    "Contract": pe_sym,
                    "Signal": "ACTIVE BUY" if (active and active["side"] == "PE") else "WAIT",
                    "Entry": active["entry"] if (active and active["side"] == "PE") else "-",
                    "Live LTP": pe_ltp if pe_ltp else "API Req",
                    "Trailing SL": active["sl"] if (active and active["side"] == "PE") else "-"
                }
            ])

    if sideways_count >= 4 and st.session_state.bot_running:
        st.warning("⚠️ MARKET SIDEWAYS ALERT: 4+ Indices tight range mein hain—naye orders automatically hold par hain.")

    total_pnl = round(st.session_state.realized_pnl + unrealized_pnl, 2)

    if total_pnl <= st.session_state.max_loss_limit and st.session_state.bot_running:
        execute_emergency_square_off(f"Max Loss Limit Crossed (₹{total_pnl:,.2f})")

    st.markdown("---")
    st.subheader("💰 Total Net P&L (All 5 Indices Combined)")
    pnl_color = "#22C55E" if total_pnl >= 0 else "#EF4444"
    st.markdown(f"<h2 style='color: {pnl_color};'>{'🟢' if total_pnl >= 0 else '🔴'} ₹{total_pnl:,.2f}</h2>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("⚙️ Engine & Safety Controls")
    if st.session_state.bot_running:
        st.info("🟢 SHIELD ACTIVE (Auto-managed: 09:15 - 03:15)")
    else:
        st.error("🔴 SHIELD STOPPED / SQUARED OFF")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("▶️ Start / Resume Shield", use_container_width=True):
            if not is_market_open:
                st.error("Market abhi band hai (09:15 - 03:15 ke beech hi start hoga).")
            else:
                st.session_state.bot_running = True
                st.session_state.danger_alarm = False
                add_log("▶️ Multi-Index Shield Started")
                st.rerun()
    with c2:
        if st.button("🚨 Emergency Square Off", type="primary", use_container_width=True):
            execute_emergency_square_off("User Pressed Emergency Kill Switch!")
            st.rerun()

st.markdown("---")

st.markdown("<p style='text-align: center; color: #64748B; font-size: 0.85rem;'>Multi-Index Pro • Nifty, BankNifty, FinNifty, Midcap & Sensex Active</p>", unsafe_allow_html=True)

