"""
app.py
------
AI Revenue Recovery Agent - Streamlit Dashboard

Entry point for the application. Run with:
    streamlit run app.py
"""

import os

import pandas as pd
import plotly.express as px
import streamlit as st

from agents.analyzer import analyze_failed_transactions
from agents.decision_agent import decide_for_dataframe
from agents.message_generator import generate_recovery_message
from models.recovery_model import RecoveryModel
from utils.data_processor import apply_filters, compute_summary_metrics, load_data

# --------------------------------------------------------------------------
# Page config + light custom styling
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="RecoverOS — AI Revenue Recovery",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Modern Matte-Black Dark Theme & Design System
# --------------------------------------------------------------------------

THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    /* Global Typography & Resets */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }

    .stAppDeployButton, [data-testid="stAppDeployButton"], footer {
        display: none !important;
    }

    /* Main Canvas Background: Liquid Dark Matte with Light Matte Red Ambient Glow */
    .stApp {
        background-color: #0D0B10 !important;
        background-image: 
            radial-gradient(circle at 50% -8%, rgba(244, 63, 94, 0.13) 0%, transparent 60%),
            radial-gradient(circle at 90% 25%, rgba(225, 29, 72, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 10% 70%, rgba(251, 113, 133, 0.06) 0%, transparent 45%),
            linear-gradient(180deg, #0F0D14 0%, #08070B 100%) !important;
        background-attachment: fixed !important;
        color: #FDFBFD !important;
    }

    /* Top Header Bar */
    [data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Sidebar: Frosted Liquid Glass Surface with Light Matte Red Border */
    [data-testid="stSidebar"] {
        background: rgba(15, 12, 19, 0.88) !important;
        backdrop-filter: blur(24px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
        border-right: 1px solid rgba(244, 63, 94, 0.25) !important;
        box-shadow: 10px 0 35px -10px rgba(0, 0, 0, 0.6) !important;
    }

    [data-testid="stSidebar"] * {
        color: #D8C8CE !important;
    }

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #FFFDFE !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* Custom Smooth Scrollbars with Light Matte Red Accent */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(13, 11, 16, 0.8);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(244, 63, 94, 0.28);
        border-radius: 6px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(244, 63, 94, 0.5);
    }

    /* Metric Cards: Pure 3D Liquid Glassmorphic Panels */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.035) !important;
        backdrop-filter: blur(24px) saturate(190%) !important;
        -webkit-backdrop-filter: blur(24px) saturate(190%) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.28) !important;
        border-bottom: 1px solid rgba(0, 0, 0, 0.45) !important;
        border-radius: 18px !important;
        padding: 22px 24px 18px 24px !important;
        box-shadow: 
            0 14px 34px -4px rgba(0, 0, 0, 0.55), 
            inset 0 1px 1px rgba(255, 255, 255, 0.18),
            inset 0 -1px 2px rgba(0, 0, 0, 0.3) !important;
        transition: transform 0.24s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.24s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.24s ease !important;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px) scale(1.005) !important;
        background: rgba(255, 255, 255, 0.055) !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
        border-top-color: rgba(255, 255, 255, 0.55) !important;
        box-shadow: 
            0 20px 42px -6px rgba(0, 0, 0, 0.7), 
            inset 0 1px 2px rgba(255, 255, 255, 0.28) !important;
    }

    div[data-testid="stMetricLabel"] {
        color: #C8B5BE !important;
        font-weight: 600 !important;
        font-size: 0.80rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        margin-bottom: 4px !important;
    }

    div[data-testid="stMetricValue"] {
        color: #FFFDFE !important;
        font-weight: 800 !important;
        font-size: 1.95rem !important;
        letter-spacing: -0.03em !important;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.4);
    }

    /* Custom Metric Card Utility */
    .metric-card {
        background: rgba(255, 255, 255, 0.035) !important;
        backdrop-filter: blur(24px) saturate(190%) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.28) !important;
        border-radius: 18px;
        padding: 22px 24px;
        color: #FFFDFE !important;
        box-shadow: 0 14px 34px -4px rgba(0, 0, 0, 0.55), inset 0 1px 1px rgba(255, 255, 255, 0.18);
    }

    /* Priority Badges */
    .priority-high {
        color: #FB7185 !important;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .priority-medium {
        color: #FBBF24 !important;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .priority-low {
        color: #34D399 !important;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    /* AI Explanation / Analysis Box: Pure Liquid Glass Panel */
    .explain-box {
        background: rgba(255, 255, 255, 0.035) !important;
        backdrop-filter: blur(24px) saturate(190%) !important;
        -webkit-backdrop-filter: blur(24px) saturate(190%) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.28) !important;
        border-left: 4px solid rgba(255, 255, 255, 0.45) !important;
        padding: 18px 22px;
        border-radius: 14px;
        font-size: 0.93rem;
        line-height: 1.6;
        color: #EDE2E6 !important;
        box-shadow: 
            0 10px 28px -4px rgba(0, 0, 0, 0.5), 
            inset 0 1px 1px rgba(255, 255, 255, 0.14);
    }

    .explain-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 700;
        font-size: 0.88rem;
        color: #FDA4AF;
        margin-bottom: 6px;
        letter-spacing: 0.02em;
    }

    /* Brand Badges */
    .synthetic-badge {
        background: rgba(244, 63, 94, 0.14);
        color: #FDA4AF;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        border: 1px solid rgba(244, 63, 94, 0.40);
        box-shadow: 0 2px 8px rgba(244, 63, 94, 0.2), inset 0 1px 0 rgba(251, 113, 133, 0.25);
        display: inline-block;
    }

    .brand-title {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1.25rem;
        font-weight: 800;
        color: #FFFDFE;
        letter-spacing: -0.02em;
        margin-bottom: 2px;
    }

    .brand-title .brand-icon {
        background: linear-gradient(135deg, #F43F5E 0%, #BE123C 100%);
        padding: 6px 8px;
        border-radius: 10px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF;
        box-shadow: 0 4px 14px rgba(244, 63, 94, 0.45), inset 0 1px 1px rgba(255, 255, 255, 0.4);
        border: 1px solid rgba(251, 113, 133, 0.4);
    }

    /* Sidebar Navigation Real Buttons - Light Matte Red Liquid Glass */
    [data-testid="stSidebar"] div.stButton {
        width: 100% !important;
        margin-bottom: -4px !important;
    }

    [data-testid="stSidebar"] div.stButton > button,
    [data-testid="stSidebar"] button[data-testid*="baseButton"] {
        width: 100% !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 12px !important;
        padding: 11px 16px !important;
        border-radius: 12px !important;
        font-size: 0.88rem !important;
        letter-spacing: -0.01em !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        cursor: pointer !important;
        text-align: left !important;
    }

    /* Target all intermediate wrapper divs inside the button to prevent centering */
    [data-testid="stSidebar"] div.stButton > button > div,
    [data-testid="stSidebar"] div.stButton > button div,
    [data-testid="stSidebar"] button[data-testid*="baseButton"] > div,
    [data-testid="stSidebar"] button[data-testid*="baseButton"] div {
        display: flex !important;
        flex-direction: row !important;
        justify-content: flex-start !important;
        align-items: center !important;
        text-align: left !important;
    }

    [data-testid="stSidebar"] div.stButton > button > div:first-child,
    [data-testid="stSidebar"] button[data-testid*="baseButton"] > div:first-child {
        width: 100% !important;
        justify-content: flex-start !important;
        gap: 12px !important;
    }

    [data-testid="stSidebar"] div.stButton > button div[data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] button[data-testid*="baseButton"] div[data-testid="stMarkdownContainer"] {
        justify-content: flex-start !important;
        text-align: left !important;
        width: auto !important;
        margin: 0 !important;
        padding: 0 !important;
        flex: 0 1 auto !important;
    }

    [data-testid="stSidebar"] div.stButton > button p,
    [data-testid="stSidebar"] button[data-testid*="baseButton"] p {
        text-align: left !important;
        margin: 0 !important;
        padding: 0 !important;
        display: inline-block !important;
        line-height: 1.2 !important;
    }

    [data-testid="stSidebar"] div.stButton > button span[data-testid="stIconMaterial"],
    [data-testid="stSidebar"] button[data-testid*="baseButton"] span[data-testid="stIconMaterial"] {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 1.25rem !important;
        margin: 0 !important;
        padding: 0 !important;
        flex-shrink: 0 !important;
        color: #C8B5BE !important;
    }

    /* Inactive (Secondary) Sidebar Navigation Buttons - Light Matte Red Frosted Glass */
    [data-testid="stSidebar"] div.stButton > button[kind="secondary"],
    [data-testid="stSidebar"] div.stButton > button[data-testid="baseButton-secondary"] {
        background: rgba(20, 16, 26, 0.65) !important;
        backdrop-filter: blur(14px) !important;
        border: 1px solid rgba(244, 63, 94, 0.22) !important;
        border-top: 1px solid rgba(251, 113, 133, 0.35) !important;
        color: #D8C8CE !important;
        font-weight: 600 !important;
        box-shadow: 
            0 4px 14px rgba(0, 0, 0, 0.35), 
            inset 0 1px 1px rgba(251, 113, 133, 0.08) !important;
    }

    [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover,
    [data-testid="stSidebar"] div.stButton > button[data-testid="baseButton-secondary"]:hover {
        background: rgba(32, 24, 40, 0.78) !important;
        border-color: #FB7185 !important;
        border-top-color: #FDA4AF !important;
        color: #FFFDFE !important;
        transform: translateX(3px) translateY(-1px) !important;
        box-shadow: 
            0 8px 22px rgba(0, 0, 0, 0.5), 
            0 0 16px rgba(244, 63, 94, 0.22), 
            inset 0 1px 1px rgba(251, 113, 133, 0.2) !important;
    }

    [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover span[data-testid="stIconMaterial"] {
        color: #FDA4AF !important;
    }

    /* Active (Primary) Sidebar Navigation Button - Light Matte Red Glowing Core */
    [data-testid="stSidebar"] div.stButton > button[kind="primary"],
    [data-testid="stSidebar"] div.stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, rgba(244, 63, 94, 0.30) 0%, rgba(190, 18, 60, 0.12) 100%) !important;
        backdrop-filter: blur(18px) !important;
        border: 1px solid #F43F5E !important;
        border-left: 4px solid #FB7185 !important;
        border-top: 1px solid rgba(251, 113, 133, 0.80) !important;
        color: #FFFDFE !important;
        font-weight: 700 !important;
        box-shadow: 
            0 8px 24px -2px rgba(244, 63, 94, 0.35), 
            0 0 20px rgba(244, 63, 94, 0.25), 
            inset 0 1px 1px rgba(251, 113, 133, 0.3) !important;
    }

    [data-testid="stSidebar"] div.stButton > button[kind="primary"] span[data-testid="stIconMaterial"] {
        color: #FB7185 !important;
    }

    /* Sidebar Filters Dedicated Box Container - Light Matte Red Frosted Glass Panel */
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="element-container"]:has(.filter-box-card) {
        background: rgba(20, 16, 26, 0.75) !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        border: 1px solid rgba(244, 63, 94, 0.35) !important;
        border-top: 1px solid rgba(251, 113, 133, 0.70) !important;
        border-radius: 16px !important;
        padding: 18px 16px !important;
        box-shadow: 
            0 12px 30px -4px rgba(0, 0, 0, 0.55), 
            0 0 20px rgba(244, 63, 94, 0.12), 
            inset 0 1px 1px rgba(251, 113, 133, 0.18) !important;
        margin-top: 8px !important;
        margin-bottom: 12px !important;
    }

    /* Permanent Visible Light Matte Red Border on ALL Dropdown Boxes & Inputs (IDLE & ACTIVE) */
    [data-testid="stSidebar"] div[data-baseweb="select"],
    [data-testid="stSidebar"] div[data-baseweb="select"] > div,
    [data-testid="stSidebar"] div[data-baseweb="select"] > div:first-child,
    [data-testid="stSidebar"] div[data-baseweb="input"],
    [data-testid="stSidebar"] div[data-baseweb="input"] > div,
    [data-testid="stSidebar"] div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
    [data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    [data-testid="stSidebar"] div[data-testid="stDateInput"] div[data-baseweb="input"] > div,
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    div[data-testid="stDateInput"] div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div:first-child,
    div[data-baseweb="input"] > div:first-child {
        background: rgba(20, 16, 25, 0.88) !important;
        background-color: rgba(20, 16, 25, 0.88) !important;
        border: 1.5px solid rgba(244, 63, 94, 0.45) !important;
        border-top: 1.5px solid rgba(251, 113, 133, 0.70) !important;
        border-bottom: 1.5px solid rgba(244, 63, 94, 0.45) !important;
        border-left: 1.5px solid rgba(244, 63, 94, 0.45) !important;
        border-right: 1.5px solid rgba(244, 63, 94, 0.45) !important;
        border-radius: 12px !important;
        min-height: 44px !important;
        color: #FDFBFD !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(251, 113, 133, 0.15) !important;
        transition: all 0.18s ease-in-out !important;
    }

    /* Hover state across all dropdowns */
    [data-testid="stSidebar"] div[data-baseweb="select"] > div:hover,
    [data-testid="stSidebar"] div[data-baseweb="input"] > div:hover,
    div[data-baseweb="select"] > div:hover,
    div[data-baseweb="input"] > div:hover {
        border-color: #FB7185 !important;
        box-shadow: 0 0 16px rgba(244, 63, 94, 0.40), inset 0 1px 1px rgba(251, 113, 133, 0.25) !important;
    }

    /* Red Theme Outline on Focused & Opened Dropdown Boxes */
    [data-testid="stSidebar"] div[data-baseweb="select"] > div:focus,
    [data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within,
    [data-testid="stSidebar"] div[data-baseweb="select"] > div[aria-expanded="true"],
    [data-testid="stSidebar"] div[data-baseweb="input"] > div:focus,
    [data-testid="stSidebar"] div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus,
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="select"] > div[aria-expanded="true"],
    div[data-baseweb="input"] > div:focus,
    div[data-baseweb="input"] > div:focus-within {
        border: 2px solid #FB7185 !important;
        border-color: #FB7185 !important;
        box-shadow: 0 0 0 3px rgba(244, 63, 94, 0.30), 0 0 22px rgba(244, 63, 94, 0.50) !important;
        outline: none !important;
    }

    /* Dropdown Popover Menu (Options List Container) */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="menu"],
    ul[role="listbox"] {
        background: rgba(18, 14, 22, 0.96) !important;
        backdrop-filter: blur(22px) saturate(190%) !important;
        -webkit-backdrop-filter: blur(22px) saturate(190%) !important;
        border: 1px solid rgba(244, 63, 94, 0.45) !important;
        border-top: 1px solid rgba(251, 113, 133, 0.80) !important;
        border-radius: 14px !important;
        box-shadow: 
            0 16px 40px -4px rgba(0, 0, 0, 0.8), 
            0 0 24px rgba(244, 63, 94, 0.22), 
            inset 0 1px 1px rgba(251, 113, 133, 0.2) !important;
        padding: 6px !important;
    }

    /* Dropdown Options List Items */
    ul[role="listbox"] li[role="option"] {
        border-radius: 8px !important;
        padding: 9px 14px !important;
        color: #EDE2E6 !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        transition: all 0.15s ease !important;
        margin: 2px 0 !important;
    }

    ul[role="listbox"] li[role="option"]:hover,
    ul[role="listbox"] li[role="option"][aria-selected="true"],
    ul[role="listbox"] li[role="option"][aria-highlighted="true"] {
        background: rgba(244, 63, 94, 0.25) !important;
        color: #FFFDFE !important;
        font-weight: 600 !important;
    }

    /* MultiSelect Tags - Light Matte Red Gradient */
    span[data-baseweb="tag"] {
        background: linear-gradient(135deg, #F43F5E 0%, #BE123C 100%) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid #FB7185 !important;
        border-top: 1px solid rgba(255, 255, 255, 0.45) !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(244, 63, 94, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
    }

    span[data-baseweb="tag"] span {
        color: #FFFDFE !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
    }

    span[data-baseweb="tag"] svg {
        fill: #FFFDFE !important;
        stroke: #FFFDFE !important;
    }

    /* DateInput Popover Calendar */
    div[data-baseweb="calendar"] {
        background: rgba(18, 14, 22, 0.96) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(244, 63, 94, 0.45) !important;
        border-top: 1px solid rgba(251, 113, 133, 0.80) !important;
        border-radius: 14px !important;
        box-shadow: 0 14px 36px rgba(0, 0, 0, 0.8), 0 0 20px rgba(244, 63, 94, 0.22) !important;
    }

    div[data-baseweb="calendar"] button[aria-selected="true"] {
        background: #F43F5E !important;
        color: #FFFDFE !important;
    }

    /* Main Area Primary Buttons: Light Matte Red Liquid Glass */
    .stApp .main .stButton > button,
    .stButton > button {
        background: linear-gradient(180deg, #F43F5E 0%, #BE123C 100%) !important;
        color: #FFFDFE !important;
        border: 1px solid rgba(251, 113, 133, 0.5) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 12px !important;
        padding: 11px 22px !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
        box-shadow: 
            0 8px 24px -2px rgba(244, 63, 94, 0.45), 
            0 0 16px rgba(244, 63, 94, 0.18),
            inset 0 1px 1px rgba(255, 255, 255, 0.35), 
            inset 0 -1px 2px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    .stApp .main .stButton > button:hover,
    .stButton > button:hover {
        background: linear-gradient(180deg, #FB7185 0%, #F43F5E 100%) !important;
        border-color: #FDA4AF !important;
        box-shadow: 
            0 12px 28px -4px rgba(244, 63, 94, 0.65), 
            0 0 22px rgba(244, 63, 94, 0.40), 
            inset 0 1px 2px rgba(255, 255, 255, 0.5) !important;
        transform: translateY(-2px) scale(1.01) !important;
    }

    .stApp .main .stButton > button:active,
    .stButton > button:active {
        transform: translateY(1px) scale(0.99) !important;
        box-shadow: 0 3px 10px rgba(244, 63, 94, 0.4) !important;
    }

    /* Dataframe & Tables: Pure 3D Liquid Glass Card */
    div[data-testid="stDataFrame"], [data-testid="stTable"] {
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 16px !important;
        overflow: hidden !important;
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.55), inset 0 1px 1px rgba(255, 255, 255, 0.12) !important;
    }

    /* Expander with Pure Liquid Glass Depth */
    div[data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.12) !important;
    }

    /* Alert / Notification boxes */
    div[data-testid="stAlert"] {
        background: rgba(255, 255, 255, 0.04) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.28) !important;
        border-radius: 14px !important;
        color: #EDE2E6 !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35) !important;
    }

    /* Horizontal Divider with Light Matte Red Specular Line */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent 0%, rgba(244, 63, 94, 0.45) 50%, transparent 100%) !important;
        margin: 1.8rem 0 !important;
    }
</style>
"""

st.markdown(THEME_CSS, unsafe_allow_html=True)


def style_fig(fig):
    """Align Plotly chart backgrounds and fonts seamlessly with dark warm liquid glass theme while preserving trace colors."""
    font_color = "#EDE2E6"
    grid_color = "rgba(251, 113, 133, 0.08)"
    zeroline_color = "rgba(251, 113, 133, 0.15)"

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=font_color, family="Plus Jakarta Sans, sans-serif", size=12),
        margin=dict(l=25, r=25, t=45, b=35),
        legend=dict(font=dict(color=font_color, size=11)),
        title=dict(font=dict(color="#FFFDFE", size=15, family="Plus Jakarta Sans, sans-serif")),
        hoverlabel=dict(
            bgcolor="#1A1420",
            bordercolor="#F43F5E",
            font=dict(color="#FFFDFE", family="Plus Jakarta Sans, sans-serif", size=12)
        )
    )
    fig.update_xaxes(
        tickfont=dict(color="#C8B5BE", size=11),
        title_font=dict(color=font_color, size=12),
        gridcolor=grid_color,
        zerolinecolor=zeroline_color
    )
    fig.update_yaxes(
        tickfont=dict(color="#C8B5BE", size=11),
        title_font=dict(color=font_color, size=12),
        gridcolor=grid_color,
        zerolinecolor=zeroline_color
    )
    fig.update_traces(
        textfont=dict(color=font_color)
    )
    return fig


DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "payments.csv")


# --------------------------------------------------------------------------
# Cached data loading + analysis pipeline
# --------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_analyzed_data(path: str) -> pd.DataFrame:
    """Load raw data, then run it through the rule-based analyzer + decision agent."""
    df = load_data(path)
    df = analyze_failed_transactions(df)

    recovery_probabilities = None
    if RecoveryModel.model_exists():
        try:
            model = RecoveryModel.load()
            failed_mask = df["payment_status"] == "Failed"
            probs = model.predict_proba(df.loc[failed_mask])
            recovery_probabilities = pd.Series(probs, index=df.loc[failed_mask].index)
        except Exception:
            recovery_probabilities = None

    df = decide_for_dataframe(df, recovery_probabilities)

    if recovery_probabilities is not None:
        df["ml_recovery_probability"] = recovery_probabilities.reindex(df.index)
    else:
        df["ml_recovery_probability"] = None

    return df


# --------------------------------------------------------------------------
# Professional SVG Icon Definitions
# --------------------------------------------------------------------------

SVG_CARD = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>'
SVG_BRAIN = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#FB7185" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>'
SVG_BOLT = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#FB7185" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
SVG_ROBOT = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FB7185" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>'
SVG_CLIPBOARD = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C8B5BE" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>'
SVG_WARNING = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FBBF24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0; margin-top: 2px;"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>'


def priority_badge(priority: str) -> str:
    if priority == "High Priority":
        return (
            '<span class="priority-high">'
            '<svg width="8" height="8" viewBox="0 0 8 8" fill="#FB7185" style="display:inline-block; vertical-align:middle; margin-right:4px;">'
            '<circle cx="4" cy="4" r="3.5"/>'
            '</svg>High Priority</span>'
        )
    elif priority == "Medium Priority":
        return (
            '<span class="priority-medium">'
            '<svg width="8" height="8" viewBox="0 0 8 8" fill="#FBBF24" style="display:inline-block; vertical-align:middle; margin-right:4px;">'
            '<circle cx="4" cy="4" r="3.5"/>'
            '</svg>Medium Priority</span>'
        )
    elif priority == "Low Priority":
        return (
            '<span class="priority-low">'
            '<svg width="8" height="8" viewBox="0 0 8 8" fill="#34D399" style="display:inline-block; vertical-align:middle; margin-right:4px;">'
            '<circle cx="4" cy="4" r="3.5"/>'
            '</svg>Low Priority</span>'
        )
    return priority or "-"


def format_inr(value: float) -> str:
    return f"₹{value:,.0f}"


# --------------------------------------------------------------------------
# Load data (with a friendly error if missing)
# --------------------------------------------------------------------------

if not os.path.exists(DATA_PATH):
    st.error(
        "No dataset found at data/payments.csv.\n\n"
        "Run `python data/generate_data.py` from the project root to generate the synthetic demo dataset."
    )
    st.stop()

df = get_analyzed_data(DATA_PATH)
model_ready = RecoveryModel.model_exists()

# --------------------------------------------------------------------------
# Sidebar navigation + filters
# --------------------------------------------------------------------------

st.sidebar.markdown(
    f"""
    <div style="padding: 4px 0 14px 0;">
        <div class="brand-title">
            <span class="brand-icon">{SVG_CARD}</span> RecoverOS
        </div>
        <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px; margin-bottom: 10px;">
            Autonomous AI Revenue Recovery
        </div>
        <span class="synthetic-badge">SYNTHETIC DEMO DATA</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.caption("Built for the Razorpay AI Buildathon 2026")

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Dashboard"

st.sidebar.markdown(
    '<div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; color: #64748B; margin-top: 10px; margin-bottom: 8px;">Navigate</div>',
    unsafe_allow_html=True,
)

NAV_CONFIG = [
    ("Dashboard", "nav_btn_dashboard", ":material/space_dashboard:"),
    ("Transaction Explorer", "nav_btn_explorer", ":material/manage_search:"),
    ("AI Recovery Center", "nav_btn_center", ":material/smart_toy:"),
    ("Analytics", "nav_btn_analytics", ":material/insights:"),
]

for label, btn_key, icon_name in NAV_CONFIG:
    is_active = (st.session_state["current_page"] == label)
    if st.sidebar.button(
        label,
        key=btn_key,
        icon=icon_name,
        use_container_width=True,
        type="primary" if is_active else "secondary",
    ):
        if st.session_state["current_page"] != label:
            st.session_state["current_page"] = label
            st.rerun()

page = st.session_state["current_page"]

st.sidebar.markdown("---")

with st.sidebar.container(border=True):
    st.markdown(
        '<div style="font-size: 0.84rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #FB7185; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">'
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#FB7185" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>'
        'Filters'
        '</div>',
        unsafe_allow_html=True,
    )

    min_date = df["transaction_date"].min().date()
    max_date = df["transaction_date"].max().date()
    date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    status_options = ["All"] + sorted(df["payment_status"].unique().tolist())
    status_sel = st.multiselect("Payment status", status_options, default=["All"])

    method_options = ["All"] + sorted(df["payment_method"].unique().tolist())
    method_sel = st.multiselect("Payment method", method_options, default=["All"])

    reason_options = ["All"] + sorted(df["failure_reason"].dropna().unique().tolist())
    reason_sel = st.multiselect("Failure reason", reason_options, default=["All"])

    priority_options = ["All"] + sorted(df["priority"].dropna().unique().tolist())
    priority_sel = st.multiselect("Priority", priority_options, default=["All"])

    segment_options = ["All"] + sorted(df["customer_segment"].unique().tolist())
    segment_sel = st.multiselect("Customer segment", segment_options, default=["All"])

filtered_df = apply_filters(
    df,
    date_range=date_range if isinstance(date_range, tuple) else None,
    payment_status=status_sel,
    payment_method=method_sel,
    failure_reason=reason_sel,
    priority=priority_sel,
    customer_segment=segment_sel,
)

if not model_ready:
    st.sidebar.warning(
        "ML recovery model not trained yet.\n\nRun `python models/train_model.py` to enable "
        "ML-based recovery probability. The app works fine without it (rule-based scoring only)."
    )

# ==========================================================================
# PAGE: DASHBOARD
# ==========================================================================

if page == "Dashboard":
    st.title("Revenue Recovery Dashboard")
    st.caption("Overview of payment performance and AI-estimated recoverable revenue.")

    metrics = compute_summary_metrics(filtered_df)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Transactions", f"{metrics['total_transactions']:,}")
    c2.metric("Successful Payments", f"{metrics['successful_transactions']:,}")
    c3.metric("Failed Payments", f"{metrics['failed_transactions']:,}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Failed Revenue", format_inr(metrics["failed_revenue"]))
    c5.metric("Potential Recoverable Revenue", format_inr(metrics["potential_recoverable_revenue"]))
    c6.metric("Recovery Rate", f"{metrics['recovery_rate']}%")

    st.markdown("### ")
    col1, col2 = st.columns(2)

    with col1:
        status_counts = filtered_df["payment_status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig = px.pie(status_counts, names="status", values="count", title="Payment Success vs Failure",
                     color="status", color_discrete_map={"Success": "#10B981", "Failed": "#F43F5E"}, hole=0.45)
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with col2:
        failed_only = filtered_df[filtered_df["payment_status"] == "Failed"]
        reason_counts = failed_only["failure_reason"].value_counts().reset_index()
        reason_counts.columns = ["failure_reason", "count"]
        fig = px.bar(reason_counts, x="failure_reason", y="count", title="Failure Reasons",
                     color="count", color_continuous_scale="Reds")
        fig.update_layout(xaxis_title="", yaxis_title="Count")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        rev_by_method = filtered_df.groupby("payment_method")["amount"].sum().reset_index()
        fig = px.bar(rev_by_method.sort_values("amount", ascending=False), x="payment_method", y="amount",
                     title="Revenue by Payment Method", color="amount", color_continuous_scale="Blues")
        fig.update_layout(xaxis_title="", yaxis_title="Revenue (₹)")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with col4:
        priority_counts = failed_only["priority"].value_counts().reset_index()
        priority_counts.columns = ["priority", "count"]
        fig = px.pie(priority_counts, names="priority", values="count", title="Recovery Priority Distribution",
                     color="priority",
                     color_discrete_map={"High Priority": "#F43F5E", "Medium Priority": "#F59E0B", "Low Priority": "#10B981"},
                     hole=0.45)
        st.plotly_chart(style_fig(fig), use_container_width=True)

    seg_failed_rev = failed_only.groupby("customer_segment")["amount"].sum().reset_index()
    fig = px.bar(seg_failed_rev.sort_values("amount", ascending=False), x="customer_segment", y="amount",
                 title="Failed Revenue by Customer Segment", color="amount", color_continuous_scale="Oranges")
    fig.update_layout(xaxis_title="", yaxis_title="Failed Revenue (₹)")
    st.plotly_chart(style_fig(fig), use_container_width=True)

    st.markdown("### Failed Transactions")
    display_cols = ["transaction_id", "customer_name", "amount", "payment_method", "failure_reason",
                     "priority", "recovery_score", "recommended_action"]
    st.dataframe(
        failed_only[display_cols].sort_values("recovery_score", ascending=False),
        use_container_width=True, hide_index=True,
    )

# ==========================================================================
# PAGE: TRANSACTION EXPLORER
# ==========================================================================

elif page == "Transaction Explorer":
    st.title("Transaction Explorer")
    st.caption("Browse every transaction and drill into a specific one for full AI analysis.")

    view_cols = ["transaction_id", "customer_name", "amount", "payment_method", "payment_status",
                 "failure_reason", "priority", "recovery_score", "recommended_action"]
    st.dataframe(filtered_df[view_cols], use_container_width=True, hide_index=True, height=350)

    st.markdown("---")
    st.subheader("Transaction Detail")

    failed_ids = filtered_df.loc[filtered_df["payment_status"] == "Failed", "transaction_id"].tolist()
    if not failed_ids:
        st.info("No failed transactions in the current filter selection.")
    else:
        selected_id = st.selectbox("Select a failed transaction to inspect", failed_ids)
        row = filtered_df.loc[filtered_df["transaction_id"] == selected_id].iloc[0]

        colA, colB = st.columns(2)
        with colA:
            st.markdown("#### Customer Information")
            st.write(f"**Name:** {row['customer_name']}")
            st.write(f"**Customer ID:** {row['customer_id']}")
            st.write(f"**Segment:** {row['customer_segment']}")
            st.write(f"**History:** {row['customer_history']}")

        with colB:
            st.markdown("#### Transaction Information")
            st.write(f"**Transaction ID:** {row['transaction_id']}")
            st.write(f"**Amount:** {format_inr(row['amount'])} ({row['currency']})")
            st.write(f"**Payment Method:** {row['payment_method']}")
            st.write(f"**Date:** {row['transaction_date']}")
            st.write(f"**Retry Count:** {row['retry_count']}")

        st.markdown("#### Failure & Recovery Analysis")
        st.write(f"**Failure Reason:** {row['failure_reason']}")
        st.markdown(f"**Priority:** {priority_badge(row['priority'])}", unsafe_allow_html=True)
        st.write(f"**Recovery Score:** {row['recovery_score']} / 100")
        if pd.notna(row.get("ml_recovery_probability")):
            st.write(f"**ML Recovery Probability:** {row['ml_recovery_probability'] * 100:.1f}%")

        st.markdown(
            f"""
            <div class="explain-box">
                <div class="explain-header">
                    {SVG_BRAIN} AI Analysis
                </div>
                <div>{row["priority_explanation"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(
            f"""
            <div class="explain-box">
                <div class="explain-header">
                    {SVG_BOLT} Recommended Action — {row["recommended_action"]}
                </div>
                <div>{row["action_explanation"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### Recovery Message")
        msg_key = f"msg_{selected_id}"
        if st.button("Generate AI Recovery Message", key=f"gen_{selected_id}"):
            with st.spinner("Generating personalized message..."):
                result = generate_recovery_message(
                    customer_name=row["customer_name"],
                    amount=row["amount"],
                    failure_reason=row["failure_reason"],
                    action=row["recommended_action"],
                    currency=row["currency"],
                    segment=row["customer_segment"],
                )
                st.session_state[msg_key] = result

        if msg_key in st.session_state:
            result = st.session_state[msg_key]
            mode_badge = (
                f'<div style="display:inline-flex; align-items:center; gap:6px; color:#A5B4FC; font-size:0.82rem; margin-top:4px;">{SVG_ROBOT} Generated by Autonomous LLM Agent</div>'
                if result["mode"] == "llm"
                else f'<div style="display:inline-flex; align-items:center; gap:6px; color:#94A3B8; font-size:0.82rem; margin-top:4px;">{SVG_CLIPBOARD} Generated from Rule-Based Template (Fallback)</div>'
            )
            st.success(result["message"])
            st.markdown(mode_badge, unsafe_allow_html=True)
            if result.get("error"):
                st.caption(f"LLM call failed, used fallback. Details: {result['error']}")

# ==========================================================================
# PAGE: AI RECOVERY CENTER
# ==========================================================================

elif page == "AI Recovery Center":
    st.title("AI Recovery Center")
    st.caption("High-priority cases and AI-recommended recovery actions, ready for outreach.")

    failed_df = filtered_df[filtered_df["payment_status"] == "Failed"].copy()
    high_priority = failed_df[failed_df["priority"] == "High Priority"].sort_values("recovery_score", ascending=False)

    m1, m2, m3 = st.columns(3)
    m1.metric("High-Priority Cases", len(high_priority))
    m2.metric("High-Priority Recoverable Value", format_inr(high_priority["amount"].sum()))
    m3.metric("Avg. Recovery Score (High Priority)", f"{high_priority['recovery_score'].mean():.1f}" if len(high_priority) else "-")

    st.markdown("### High-Priority Recovery Cases")
    st.dataframe(
        high_priority[["transaction_id", "customer_name", "amount", "failure_reason",
                        "recovery_score", "recommended_action"]],
        use_container_width=True, hide_index=True,
    )

    st.markdown("### AI Recommendations Breakdown")
    action_counts = failed_df["recommended_action"].value_counts().reset_index()
    action_counts.columns = ["recommended_action", "count"]
    fig = px.bar(action_counts.sort_values("count", ascending=True), x="count", y="recommended_action",
                 orientation="h", title="Recommended Actions Across All Failed Transactions",
                 color="count", color_continuous_scale="Purples")
    fig.update_layout(yaxis_title="", xaxis_title="Number of transactions")
    st.plotly_chart(style_fig(fig), use_container_width=True)

    st.markdown("### Batch Message Generation")
    st.caption("Generate recovery messages for the top High-Priority cases in one click.")

    top_n = st.slider("How many top cases to generate messages for?", 1, min(10, max(len(high_priority), 1)), min(3, max(len(high_priority), 1)))

    if st.button("Generate messages for top cases"):
        top_cases = high_priority.head(top_n)
        for _, row in top_cases.iterrows():
            with st.spinner(f"Generating message for {row['customer_name']}..."):
                result = generate_recovery_message(
                    customer_name=row["customer_name"],
                    amount=row["amount"],
                    failure_reason=row["failure_reason"],
                    action=row["recommended_action"],
                    currency=row["currency"],
                    segment=row["customer_segment"],
                )
            with st.expander(f"{row['customer_name']} — {row['transaction_id']} ({format_inr(row['amount'])})"):
                st.write(f"**Action:** {row['recommended_action']}")
                st.info(result["message"])
                badge_html = (
                    f'<div style="display:inline-flex; align-items:center; gap:6px; color:#A5B4FC; font-size:0.82rem;">{SVG_ROBOT} LLM-generated</div>'
                    if result["mode"] == "llm"
                    else f'<div style="display:inline-flex; align-items:center; gap:6px; color:#94A3B8; font-size:0.82rem;">{SVG_CLIPBOARD} Template fallback</div>'
                )
                st.markdown(badge_html, unsafe_allow_html=True)

# ==========================================================================
# PAGE: ANALYTICS
# ==========================================================================

elif page == "Analytics":
    st.title("Analytics")
    st.caption("Deeper revenue recovery estimation and model performance.")

    metrics = compute_summary_metrics(filtered_df)

    st.markdown("### Revenue Recovery Estimation")
    est_df = pd.DataFrame(
        {
            "Metric": [
                "Total Transaction Value", "Successful Revenue", "Failed Revenue",
                "Potential Recoverable Revenue", "High-Priority Recoverable Revenue", "Recovery Rate",
            ],
            "Value": [
                format_inr(metrics["total_value"]), format_inr(metrics["successful_revenue"]),
                format_inr(metrics["failed_revenue"]), format_inr(metrics["potential_recoverable_revenue"]),
                format_inr(metrics["high_priority_recoverable_revenue"]), f"{metrics['recovery_rate']}%",
            ],
        }
    )
    st.table(est_df)

    st.markdown("### Recovery Rate Trend (by day)")
    daily = filtered_df.copy()
    daily["date"] = daily["transaction_date"].dt.date
    daily_failed = daily[daily["payment_status"] == "Failed"].groupby("date")["amount"].sum()
    daily_recoverable = (
        daily[daily["payment_status"] == "Failed"]
        .assign(recoverable=lambda d: d["amount"] * (d["recovery_score"].fillna(0) / 100))
        .groupby("date")["recoverable"].sum()
    )
    trend = pd.DataFrame({"Failed Revenue": daily_failed, "Recoverable Revenue": daily_recoverable}).fillna(0).reset_index()
    if len(trend):
        fig = px.line(trend, x="date", y=["Failed Revenue", "Recoverable Revenue"], title="Failed vs Recoverable Revenue Over Time")
        st.plotly_chart(style_fig(fig), use_container_width=True)
    else:
        st.info("No data in the current filter range to plot a trend.")

    st.markdown("### ML Model Performance")
    if model_ready:
        try:
            model = RecoveryModel.load()
            importances = model.feature_importances().head(10)
            fig = px.bar(importances[::-1], orientation="h", title="Top Feature Importances (Recovery Likelihood Model)")
            fig.update_layout(yaxis_title="", xaxis_title="Importance", showlegend=False)
            st.plotly_chart(style_fig(fig), use_container_width=True)
            st.caption(
                "This RandomForest model was trained on historical failed transactions to predict the "
                "probability that a retry/follow-up will succeed. Run `python models/train_model.py` "
                "to retrain and see evaluation metrics (accuracy, precision, recall, ROC-AUC) in the terminal."
            )
        except Exception as exc:
            st.warning(f"Could not load model details: {exc}")
    else:
        st.info("Train the model with `python models/train_model.py` to see feature importance here.")

st.markdown("---")
st.markdown(
    f"""
    <div style="display: flex; align-items: flex-start; gap: 8px; font-size: 0.8rem; color: #64748B; padding-top: 4px; padding-bottom: 24px;">
        {SVG_WARNING}
        <span>All transaction and customer data shown is synthetically generated for demonstration purposes only. This project is not officially affiliated with or connected to Razorpay's live payment systems.</span>
    </div>
    """,
    unsafe_allow_html=True,
)

