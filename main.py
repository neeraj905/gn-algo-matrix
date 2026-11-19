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
# PART 2: MAIN PAGE DEMAT USER & ID (PER-DEVICE + REFRESH SAFE + ANGEL HOOK)
# ==============================================================================
def fetch_demat_holder_from_angel(client_id: str) -> str:
    """
    angel_api.py se connected profile/session ke zariye is Client ID ka holder name laata hai.
    Agar abhi live broker session connected nahi hai, toh pending status return karta hai.
    """
    if not client_id:
        return ""
    # Agar angel_api.py mein koi function/session holder name de raha hai toh yahan se aayega:
    # try:
    #     from angel_api import get_profile_name
    #     name = get_profile_name(client_id)
    #     if name:
    #         return str(name).strip().upper()
    # except Exception:
    #     pass
    return st.session_state.get(f"holder_name_{client_id}", "DEMAT ACCOUNT VERIFICATION PENDING")

# Sirf isi browser/device ke URL query param se ID uthao (refresh ke baad bhi yahi rahegi)
url_cid = st.query_params.get("cid", "").strip().upper()

if "active_client_id" not in st.session_state:
    st.session_state["active_client_id"] = url_cid
elif url_cid and not st.session_state["active_client_id"]:
    st.session_state["active_client_id"] = url_cid

current_cid = st.session_state["active_client_id"]
if current_cid and st.query_params.get("cid", "") != current_cid:
    st.query_params["cid"] = current_cid

def _on_main_cid_submit():
    entered_cid = st.session_state.get("main_cid_input", "").strip().upper()
    st.session_state["active_client_id"] = entered_cid
    if entered_cid:
        st.query_params["cid"] = entered_cid
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

st.text_input(
    "DEMAT CLIENT ID",
    value=current_cid,
    key="main_cid_input",
    on_change=_on_main_cid_submit,
    placeholder="Enter Client ID"
)

active_cid = st.session_state["active_client_id"]
if active_cid:
    holder_name = fetch_demat_holder_from_angel(active_cid)
    st.markdown(f"""
    <div style="
        text-align: left;
        color: #F8FAFC;
        font-weight: 900;
        font-size: 1.05rem;
        margin-top: 8px;
        margin-bottom: 10px;
    ">
        {holder_name} &nbsp;|&nbsp; ID: {active_cid}
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")





