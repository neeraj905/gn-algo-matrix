# ==============================================================================
# PART 0: IMPORTS & PAGE CONFIGURATION
# ==============================================================================
import streamlit as st

st.set_page_config(
    page_title="Algo Trading Portal",
    page_icon="🛡️",
    layout="centered"
)

# ==============================================================================
# PART 1: BIG BOLD RICH METALLIC GOLD HEADER
# ==============================================================================
st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
    }
</style>

<div style="text-align: center; padding: 14px 0 6px 0;">
    <h1 style="
        font-size: 3.1rem;
        font-weight: 900;
        letter-spacing: 2.5px;
        margin: 0;
        line-height: 1.18;
        background: linear-gradient(180deg, #FFFBEB 0%, #FDE047 38%, #EAB308 72%, #A16207 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0px 2px 10px rgba(234, 179, 8, 0.28));
    ">
        ALGO TRADING<br>PORTAL
    </h1>
    <p style="
        color: #CBD5E1;
        font-size: 1rem;
        font-weight: 600;
        margin-top: 12px;
        margin-bottom: 14px;
    ">
        King Shield Pro • Trailing SL &amp; 25% Capital Guard
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==============================================================================
# PART 2: CLIENT ID & DEMAT ACCOUNT HOLDER (NO HARDCODED NAME)
# ==============================================================================
saved_client_id = st.query_params.get("cid", "").strip().upper()

if "client_id" not in st.session_state:
    st.session_state["client_id"] = saved_client_id

if st.session_state["client_id"] and st.query_params.get("cid", "") != st.session_state["client_id"]:
    st.query_params["cid"] = st.session_state["client_id"]

def _on_client_id_change():
    entered = st.session_state.get("client_id_input", "").strip().upper()
    st.session_state["client_id"] = entered
    if entered:
        st.query_params["cid"] = entered
    elif "cid" in st.query_params:
        del st.query_params["cid"]

st.text_input(
    "Enter Client ID",
    value=st.session_state["client_id"],
    key="client_id_input",
    on_change=_on_client_id_change,
    placeholder="Apni Demat Client ID daalein"
)

active_cid = st.session_state["client_id"]

if active_cid:
    # Aage broker session connect hone par yahan usi demat account ka live name aayega
    demat_holder_name = st.session_state.get("demat_holder_name") or "Awaiting Demat Account Verification"

    st.markdown(f"""
    <div style="
        background: #1e293b;
        padding: 14px 16px;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-top: 10px;
        margin-bottom: 14px;
    ">
        <div style="color: #94A3B8; font-size: 0.78rem; font-weight: 700; letter-spacing: 1px;">
            DEMAT ACCOUNT HOLDER
        </div>
        <div style="color: #F8FAFC; font-size: 1.15rem; font-weight: 800; margin-top: 4px;">
            {demat_holder_name}
        </div>
        <div style="color: #38BDF8; font-size: 0.88rem; font-weight: 700; margin-top: 4px;">
            CLIENT ID: {active_cid}
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Apni Demat Client ID daalein — refresh karne par bhi yahi bani rahegi.")

st.markdown("---")




