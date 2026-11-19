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
# PART 1: DARK THEME & SOFT METALLIC GOLD HEADER
# ==============================================================================
st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
    }
</style>

<div style="text-align: center; padding: 10px 0 5px 0;">
    <h1 style="
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: 2px;
        margin: 0;
        line-height: 1.25;
        background: linear-gradient(180deg, #FEF9C3 0%, #FACC15 52%, #CA8A04 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    ">
        ALGO TRADING<br>PORTAL
    </h1>
    <p style="
        color: #CBD5E1;
        font-size: 0.95rem;
        font-weight: 500;
        margin-top: 10px;
        margin-bottom: 12px;
    ">
        King Shield Pro • Trailing SL &amp; 25% Capital Guard
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")


