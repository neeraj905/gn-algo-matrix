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
st.markdown("---")

if st.session_state.danger_alarm:
    st.markdown(f'<div class="danger-beacon">🚨 KHATRE KI GHANTI / DANGER ALERT 🚨<br><span style="font-size:0.9rem;">{st.session_state.danger_reason}</span></div>', unsafe_allow_html=True)
    c_al1, c_al2 = st.columns(2)
    with c_al1:
        if st.button("🛑 SABHI ORDERS EXIT KAREIN", type="primary", use_container_width=True):
            execute_emergency_square_off("User Triggered Emergency Exit From Alarm!")
            st.rerun()
    with c_al2:
        if st.button("🔕 Sirf Siren Band Karein", use_container_width=True):
            st.session_state.danger_alarm = False
            st.session_state.danger_reason = ""
            st.rerun()

if st.session_state.broker_connected:
    user_title = f"{st.session_state.selected_broker.upper()} • {st.session_state.creds.get('client_id', '')}"
    user_sub = f"Mode: {st.session_state.trading_mode} | 1-Sec Scanner Active"
else:
    user_title = "GUEST / UNCONNECTED"
    user_sub = "Upar '🔑 Broker Account Settings' par tap karke apna broker jodein"

st.markdown(f'<div class="shield-box"><div style="font-size:0.75rem;color:#94A3B8;">ACTIVE USER & BROKER</div><div style="font-size:1.1rem;font-weight:bold;color:#F8FAFC;">👤 {user_title}</div><div style="font-size:0.85rem;color:#38BDF8;">{user_sub}</div></div>', unsafe_allow_html=True)

if is_market_open:
    st.success(f"🟢 {market_msg}")
else:
    st.warning(f"🟠 {market_msg}")

total_balance = st.session_state.broker_handler.get_balance() if st.session_state.broker_connected else 100000.0
risk_cap = total_balance * 0.25
safe_reserve = total_balance * 0.75

col1, col2, col3 = st.columns(3)
col1.metric("TOTAL BALANCE", f"₹{total_balance:,.2f}")
col2.metric("25% RISK CAP", f"₹{risk_cap:,.2f}")
col3.metric("75% SAFE RESERVE", f"₹{safe_reserve:,.2f}")

if menu_option == "🔑 Broker Account Settings":
    st.subheader("⚙️ Trading Mode & Risk Limits")
    st.session_state.trading_mode = st.radio("Trading Mode", ["PAPER (Safe Test)", "LIVE REAL MONEY"], index=0 if st.session_state.trading_mode == "PAPER (Safe Test)" else 1, horizontal=True)
    st.session_state.lots_per_index = st.number_input("Lots Per Index", min_value=1, max_value=20, value=int(st.session_state.lots_per_index))
    st.session_state.max_loss_limit = st.number_input("Max Daily Loss Alarm Limit (₹)", value=float(st.session_state.max_loss_limit), step=100.0)
    st.markdown("---")
    st.subheader("🔑 Select & Connect Your Broker")
    brokers_list = ["Angel One", "Kotak Neo", "Dhan", "Zerodha Kite", "Upstox"]
    default_idx = brokers_list.index(st.session_state.selected_broker) if st.session_state.selected_broker in brokers_list else 0
    chosen_broker = st.selectbox("Apna Broker Chunein", brokers_list, index=default_idx)
    prev = st.session_state.creds
    new_creds = {}
    if chosen_broker == "Angel One":
        new_creds["client_id"] = st.text_input("Angel Client ID", value=prev.get("client_id", ""))
        new_creds["api_key"] = st.text_input("SmartAPI Key", value=prev.get("api_key", ""), type="password")
        new_creds["password"] = st.text_input("MPIN / Password", value=prev.get("password", ""), type="password")
        new_creds["totp_secret"] = st.text_input("TOTP Secret Key", value=prev.get("totp_secret", ""), type="password")
    elif chosen_broker == "Kotak Neo":
        new_creds["client_id"] = st.text_input("Kotak UCC (Client ID)", value=prev.get("client_id", ""))
        new_creds["mobile_number"] = st.text_input("Registered Mobile (+91...)", value=prev.get("mobile_number", ""))
        new_creds["access_token"] = st.text_input("Neo Access Token", value=prev.get("access_token", ""), type="password")
        new_creds["password"] = st.text_input("MPIN", value=prev.get("password", ""), type="password")
        new_creds["totp_secret"] = st.text_input("TOTP Secret Key", value=prev.get("totp_secret", ""), type="password")
    elif chosen_broker == "Dhan":
        new_creds["client_id"] = st.text_input("Dhan Client ID", value=prev.get("client_id", ""))
        new_creds["access_token"] = st.text_input("Dhan Access Token", value=prev.get("access_token", ""), type="password")
    elif chosen_broker in ["Zerodha Kite", "Upstox"]:
        new_creds["client_id"] = st.text_input(f"{chosen_broker} User ID", value=prev.get("client_id", ""))
        new_creds["api_key"] = st.text_input("API Key", value=prev.get("api_key", ""), type="password")
        new_creds["access_token"] = st.text_input("Daily Access Token", value=prev.get("access_token", ""), type="password")
    if st.button("💾 Save & Connect Broker", use_container_width=True):
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
                    st.query_params["session"] = base64.urlsafe_b64encode(payload.encode()).decode()
                    add_log(f"Connected {chosen_broker}: {new_creds.get('client_id')}")
                    st.success(f"{msg} (Saved!)")
                    st.rerun()
                else:
                    st.error(f"Failed: {msg}")
        else:
            st.warning("Kripya saari fields bharein.")
    if st.session_state.broker_connected:
        st.success(f"🟢 Connected: {st.session_state.selected_broker} ({st.session_state.creds.get('client_id')})")
        if st.button("🗑️ Disconnect & Clear Account"):
            st.query_params.clear()
            st.session_state.broker_connected = False
            st.session_state.creds = {}
            st.session_state.broker_handler = None
            st.rerun()

elif menu_option == "📜 Execution Logs":
    st.subheader("📜 Live 1-Sec Scanner & Execution Logs")
    for log in st.session_state.logs or ["Abhi koi log nahi hai."]:
        st.text(log)

else:
    st.subheader("📡 1-Second Live Market Scanner (All 5 Indices)")
    engine = st.session_state.market_engine
    handler = st.session_state.broker_handler
    unrealized_pnl = 0.0
    sideways_count = 0
    crash_detected = False
    crash_index = ""

    for idx_name in INDEX_CONFIG.keys():
        spot, chg_pct = engine.get_live_spot_and_change(idx_name, handler)
        prev_spot = st.session_state.prev_spots.get(idx_name, spot)
        if spot:
            st.session_state.prev_spots[idx_name] = spot
        tick_up = (spot >= prev_spot) if (spot and prev_spot) else (chg_pct >= 0)
        num_color = "#22C55E" if (chg_pct >= 0 and tick_up) else "#EF4444"
        arrow = "▲" if chg_pct >= 0 else "▼"

        if chg_pct <= -0.85:
            crash_detected = True
            crash_index = f"{idx_name} ({chg_pct:+.2f}%)"

        signal = engine.evaluate_signal(chg_pct)
        if signal == "SIDEWAYS":
            sideways_count += 1

        ce_contract, pe_contract = engine.get_atm_option_contracts(idx_name, spot) if spot else (None, None)
        ce_sym = ce_contract["symbol"] if ce_contract else f"{idx_name} ATM CE"
        pe_sym = pe_contract["symbol"] if pe_contract else f"{idx_name} ATM PE"
        ce_ltp = handler.get_ltp(ce_contract["exchange"], ce_sym, ce_contract["token"]) if (handler and hasattr(handler, "get_ltp") and ce_contract) else None
        pe_ltp = handler.get_ltp(pe_contract["exchange"], pe_sym, pe_contract["token"]) if (handler and hasattr(handler, "get_ltp") and pe_contract) else None

        active = st.session_state.active_trades.get(idx_name)
        idx_pnl = 0.0
        if active:
            curr_ltp = ce_ltp if active["side"] == "CE" else pe_ltp
            if curr_ltp:
                idx_pnl = round((curr_ltp - active["entry"]) * active["qty"], 2)
                if curr_ltp > active["highest"]:
                    active["highest"] = curr_ltp
                    new_sl = round(curr_ltp * 0.95, 2)
                    if new_sl > active["sl"]:
                        active["sl"] = new_sl
                        add_log(f"📈 TRAIL SL UP {active['symbol']}: New SL ₹{active['sl']} (High: ₹{curr_ltp})")
                if curr_ltp <= active["sl"]:
                    if st.session_state.trading_mode == "LIVE REAL MONEY" and handler:
                        ok_exit, exit_res = handler.place_limit_order(active["symbol"], active["token"], "SELL", active["qty"], max(0.05, curr_ltp * 0.98), active["exchange"])
                        if not ok_exit:
                            trigger_danger_alarm(f"EXIT ORDER FAILED ({active['symbol']}): {exit_res}")
                    st.session_state.realized_pnl += idx_pnl
                    add_log(f"🛑 5% SL EXIT {active['symbol']} @ ₹{curr_ltp} | P&L: ₹{idx_pnl}")
                    del st.session_state.active_trades[idx_name]
                    active = None

        if not active and st.session_state.bot_running and not st.session_state.capital_locked and is_market_open and signal in ["BUY_CE", "BUY_PE"]:
            chosen = ce_contract if signal == "BUY_CE" else pe_contract
            entry_ltp = ce_ltp if signal == "BUY_CE" else pe_ltp
            if chosen and entry_ltp and entry_ltp > 5.0:
                qty = chosen["lot_size"] * int(st.session_state.lots_per_index)
                if (entry_ltp * qty) <= risk_cap:
                    order_ok = True
                    if st.session_state.trading_mode == "LIVE REAL MONEY" and handler:
                        order_ok, oid = handler.place_limit_order(chosen["symbol"], chosen["token"], "BUY", qty, round(entry_ltp * 1.01, 2), chosen["exchange"])

