import streamlit as st
import pandas as pd
import random
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Algo Trading Portal - Multi Index Pro",
                   page_icon="🛡️", layout="wide")

IST = ZoneInfo("Asia/Kolkata")
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=5000, key="portal_refresh")
except ImportError:
    pass

st.markdown("""
<style>
.stApp{background:#0F172A;color:#F8FAFC}
#MainMenu,footer{visibility:hidden}
.golden-title{text-align:center;font-size:2.25rem;font-weight:900;color:#E7C66A}
.subtitle{text-align:center;color:#94A3B8}
.index-header{background:#1E293B;border-left:4px solid #38BDF8;
border-radius:6px;padding:9px 12px;margin-top:14px;font-weight:800}
.big-number{font-size:1.55rem;font-weight:850}
.up{color:#22C55E!important}.down{color:#EF4444!important}
.flat{color:#CBD5E1!important}
.signal-box{border:2px solid;border-radius:12px;padding:14px;
text-align:center;margin:10px 0;font-weight:900}
.signal-dot{display:inline-block;width:17px;height:17px;border-radius:50%;
margin-right:8px;vertical-align:middle}
div.stButton>button{width:100%;min-height:48px;font-weight:800}
</style>
""", unsafe_allow_html=True)

DEFAULT_INDEX = {
    "NIFTY": {"spot":22612.50,"previous":22612.50,"ce":138.25,"pe":88.50},
    "BANKNIFTY": {"spot":48250.00,"previous":48250.00,"ce":345.00,"pe":290.00},
    "FINNIFTY": {"spot":21400.00,"previous":21400.00,"ce":112.50,"pe":95.00},
    "MIDCAPNIFTY": {"spot":10850.00,"previous":10850.00,"ce":68.00,"pe":54.50},
    "SENSEX": {"spot":74500.00,"previous":74500.00,"ce":520.00,"pe":480.00},
}
if "idx_states" not in st.session_state:
    st.session_state.idx_states = DEFAULT_INDEX
if "paper_running" not in st.session_state:
    st.session_state.paper_running = False
if "emergency_latched" not in st.session_state:
    st.session_state.emergency_latched = False
if "last_update" not in st.session_state:
    st.session_state.last_update = None

now = datetime.now(IST)
market_open = (now.weekday() < 5 and
               dtime(9,15) <= now.time() <= dtime(15,30))
if now.weekday() >= 5:
    market_message = "Market Closed - Weekend"
elif now.time() < dtime(9,15):
    market_message = "Pre-Market"
elif now.time() > dtime(15,30):
    market_message = "Market Closed - Post Market"
else:
    market_message = "Market Open"

# Simulated values only: no live exchange feed and no broker orders.
if market_open and st.session_state.paper_running and not st.session_state.emergency_latched:
    for item in st.session_state.idx_states.values():
        item["previous"] = item["spot"]
        item["spot"] = round(max(1, item["spot"] + random.uniform(-15,16.5)),2)
        item["ce"] = round(max(1,item["ce"] + random.uniform(-4.5,5.2)),2)
        item["pe"] = round(max(1,item["pe"] + random.uniform(-4.5,5.2)),2)
    st.session_state.last_update = now

alerts = []
for name, item in st.session_state.idx_states.items():
    spot, previous = item.get("spot"), item.get("previous")
    if not isinstance(spot,(int,float)) or not isinstance(previous,(int,float)) or spot <= 0 or previous <= 0:
        alerts.append(f"{name}: Invalid price data")
    else:
        move_pct = (spot-previous)/previous*100
        if abs(move_pct) >= 0.8:
            alerts.append(f"{name}: Unusual simulated move ({move_pct:+.2f}%)")

if st.session_state.emergency_latched:
    alert_text, alert_color = "EMERGENCY STOP ACTIVE", "#EF4444"
elif alerts:
    alert_text, alert_color = "SYSTEM WARNING", "#EF4444"
elif not market_open:
    alert_text, alert_color = "MARKET CLOSED", "#F59E0B"
else:
    alert_text, alert_color = "SYSTEM NORMAL", "#22C55E"

st.markdown('<div class="golden-title">ALGO TRADING PORTAL</div>',unsafe_allow_html=True)
st.markdown('<div class="subtitle">Multi-Index Pro • Paper Dashboard</div>',unsafe_allow_html=True)
st.warning("PAPER / DEMO MODE ONLY: prices and P&L are simulated. No broker orders are placed.")
st.divider()

st.markdown(f"""
<div class="signal-box" style="border-color:{alert_color};
background:{alert_color}18;color:{alert_color}">
<span class="signal-dot" style="background:{alert_color}"></span>
{alert_text}
<div style="font-size:.82rem;font-weight:normal;margin-top:5px">
Separate system warning signal — not market direction
</div></div>""",unsafe_allow_html=True)

for message in alerts:
    st.error("⚠️ " + message)
if st.session_state.emergency_latched:
    st.error("Paper engine stopped. Review the system before resuming.")
elif not market_open:
    st.info(market_message)
else:
    st.success("No demo-system warning currently detected.")

a,b,c = st.columns(3)
a.metric("Market Status",market_message)
b.metric("Paper Engine","RUNNING" if st.session_state.paper_running else "STOPPED")
c.metric("Dashboard Time (IST)",now.strftime("%I:%M:%S %p"))
st.caption("Last simulated update: " + (
    st.session_state.last_update.strftime("%d-%m-%Y %I:%M:%S %p")
    if st.session_state.last_update else "No update yet"))

st.subheader("📊 Multi-Index Matrix — Green = Up, Red = Down")
total_pnl = 0.0
for name,item in st.session_state.idx_states.items():
    delta = item["spot"]-item["previous"]
    pct = delta/item["previous"]*100 if item["previous"] else 0
    if delta > 0:
        css, arrow = "up","▲"
    elif delta < 0:
        css, arrow = "down","▼"
    else:
        css, arrow = "flat","●"
    st.markdown(f'<div class="index-header">{name}</div>',unsafe_allow_html=True)
    st.markdown(
        f'<div class="big-number {css}">{item["spot"]:,.2f} '
        f'{arrow} {delta:+,.2f} ({pct:+.2f}%)</div>',
        unsafe_allow_html=True)

    ce_pnl = round((item["ce"]-120.0)*25,2)
    pe_pnl = round((item["pe"]-80.0)*25,2)
    total_pnl += ce_pnl+pe_pnl
    df = pd.DataFrame([
        {"Instrument":name+" CE","Type":"DEMO CALL","Demo Entry":120.0,
         "Demo LTP":item["ce"],"Demo P&L":ce_pnl},
        {"Instrument":name+" PE","Type":"DEMO PUT","Demo Entry":80.0,
         "Demo LTP":item["pe"],"Demo P&L":pe_pnl},
    ])
    st.dataframe(df,use_container_width=True,hide_index=True,
        column_config={
            "Demo Entry":st.column_config.NumberColumn(format="₹%.2f"),
            "Demo LTP":st.column_config.NumberColumn(format="₹%.2f"),
            "Demo P&L":st.column_config.NumberColumn(format="₹%.2f")})

st.divider()
st.subheader("💰 Combined Demo P&L")
pnl_css = "up" if total_pnl >= 0 else "down"
st.markdown(f'<div class="big-number {pnl_css}">₹{total_pnl:,.2f}</div>',
            unsafe_allow_html=True)
st.caption("Illustrative calculation only; not actual holdings or account P&L.")

st.divider()
st.subheader("⚙️ Paper Engine & Emergency Controls")
start_col, stop_col = st.columns(2)
with start_col:
    if st.button("▶ START / RESUME PAPER ENGINE"):
        if st.session_state.emergency_latched:
            st.warning("Emergency stop is latched. Review and reset it first.")
        else:
            st.session_state.paper_running = True
            st.rerun()
with stop_col:
    if st.button("🚨 EMERGENCY STOP",type="primary"):
        st.session_state.paper_running = False
        st.session_state.emergency_latched = True
        st.rerun()

if st.session_state.emergency_latched:
    st.error("EMERGENCY STOP ACTIVE — paper simulation is stopped.")
    if st.button("Reset Emergency (after review)"):
        st.session_state.emergency_latched = False
        st.session_state.paper_running = False
        st.rerun()

st.caption("Emergency Stop halts this local paper simulation only. It does not cancel, close, or square off broker orders.")

st.divider()
st.subheader("🔐 Broker Settings & Multi-Device Sync")
st.info("Secure broker credential storage and syncing the same user's data across phones require authenticated backend services and an encrypted database. This single-file demo does not save API keys, PINs, passwords or TOTP secrets.")
st.caption("Market numbers: green = up, red = down, grey = unchanged. Separate red system signal = warning / emergency condition.")
st.markdown('<div style="text-align:center;color:#64748B;padding:12px">Multi-Index Pro • Paper Dashboard</div>',unsafe_allow_html=True)
