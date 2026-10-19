import streamlit as st
import random
import time

# Page Configuration & Rich Charcoal Navy Theme Setup
st.set_page_config(
    page_title="Algo Trading Portal",
    page_icon="📈",
    layout="centered"
)

# Custom CSS for Soft Dark Blue-Gray Background, 4x Bold Golden Title, and Trading Colors
st.markdown("""
    <style>
    /* Main Background: Soft Dark Blue-Gray / Rich Charcoal Navy */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    
    /* 4x Larger, Bold, Glowing Golden Title */
    .golden-title {
        font-size: 3.2rem !important;
        font-weight: 900 !important;
        background: linear-gradient(90deg, #BF953F, #FCF6BA, #B38728, #FBF5B7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
        padding-top: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .subtitle {
        text-align: center;
        color: #94A3B8;
        font-size: 1.1rem;
        margin-bottom: 30px;
        letter-spacing: 1px;
    }
    
    /* Trading Card Styling */
    .metric-box {
        background-color: #1E293B;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Header Section with 4x Larger Golden Title
st.markdown('<p class="golden-title">ALGO TRADING PORTAL</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Professional Automated Trading Terminal</p>', unsafe_allow_html=True)

st.divider()

# Live Market Data Simulation with Dynamic Green/Red Colors
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Live Nifty Index")
    nifty_price = 24350.25 + round(random.uniform(-5.0, 5.0), 2)
    nifty_change = round(random.uniform(-20.0, 35.0), 2)
    color_style = "color: #22C55E; font-weight: bold;" if nifty_change >= 0 else "color: #EF4444; font-weight: bold;"
    sign_str = "+" if nifty_change >= 0 else ""
    
    st.markdown(f"<h2>{nifty_price:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='{color_style}'>{sign_str}{nifty_change} ({sign_str}{nifty_change/200:.2f}%)</p>", unsafe_allow_html=True)

with col2:
    st.markdown("### Paper Portfolio P&L")
    pnl_value = 12450.00 + round(random.uniform(-100.0, 150.0), 2)
    pnl_color = "color: #22C55E; font-weight: bold;" if pnl_value >= 0 else "color: #EF4444; font-weight: bold;"
    pnl_sign = "+" if pnl_value >= 0 else ""
    
    st.markdown(f"<h2>{pnl_value:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='{pnl_color}'>{pnl_sign}{pnl_value * 0.01:.2f}</p>", unsafe_allow_html=True)

st.divider()

# Status and Bot Controls
st.info("Paper Trading Mode Active: Orders will be simulated safely without real capital risk.")

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("Start Paper Bot", use_container_width=True):
        st.success("Paper Trading Bot Started Successfully!")

with col_btn2:
    if st.button("Stop Paper Bot", use_container_width=True):
        st.warning("Paper Trading Bot Stopped.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748B; font-size: 0.85rem;'>Powered by Cloud Web Engine • Secure & Real-time</p>", unsafe_allow_html=True)
