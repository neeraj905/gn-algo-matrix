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



