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
# PART 2: FULL CLIENT ID OPTIONS (MAIN + SIDEBAR + SAVE + CLEAR + REFRESH SAFE)
# ==============================================================================
url_cid = st.query_params.get("cid", "").strip().upper()
if "active_client_id" not in st.session_state:
    st.session_state["active_client_id"] = url_cid
elif url_cid and not st.session_state["active_client_id"]:
    st.session_state["active_client_id"] = url_cid

current_cid = st.session_state["active_client_id"]
if current_cid and st.query_params.get("cid", "") != current_cid:
    st.query_params["cid"] = current_cid

def _set_cid(new_val: str):
    cleaned = new_val.strip().upper()
    st.session_state["active_client_id"] = cleaned
    if cleaned:
        st.query_params["cid"] = cleaned
    elif "cid" in st.query_params:
        del st.query_params["cid"]

st.markdown("""
<style>
    div[data-testid="stTextInput"] label {
        color: #F8FAFC !important;
        font-weight: 900 !important;
        font-size: 1rem !important;
    }
    div[data-testid="stTextInput"] input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        border: 1px solid #64748b !important;
        border-radius: 10px !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }
</style>
""", unsafe_allow_html=True)

# Option 1: Left Side (Sidebar) mein Client ID option
with st.sidebar:
    st.markdown("**CLIENT ID**")
    side_val = st.text_input(
        "Sidebar Client ID",
        value=current_cid,
        key="side_cid_input",
        label_visibility="collapsed",
        placeholder="Enter Client ID"
    )
    if st.button("Apply ID", key="side_apply_btn", use_container_width=True):
        _set_cid(side_val)
        st.rerun()
    if st.button("Clear ID", key="side_clear_btn", use_container_width=True):
        _set_cid("")
        st.rerun()

# Option 2: Main Page par Client ID box + Save & Clear buttons
main_val = st.text_input(
    "DEMAT CLIENT ID",
    value=current_cid,
    key="main_cid_input",
    placeholder="Enter Client ID"
)

col_save, col_clear = st.columns(2)
with col_save:
    if st.button("Save ID", key="main_save_btn", use_container_width=True):
        _set_cid(main_val)
        st.rerun()
with col_clear:
    if st.button("Clear ID", key="main_clear_btn", use_container_width=True):
        _set_cid("")
        st.rerun()

active_cid = st.session_state["active_client_id"]
if active_cid:
    holder_name = st.session_state.get(f"holder_name_{active_cid}") or "DEMAT ACCOUNT VERIFICATION PENDING"
    st.markdown(f"**{holder_name} | ID: {active_cid}**")

st.markdown("---")
    





