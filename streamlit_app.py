import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
import google.generativeai as genai
from dotenv import load_dotenv
import base64
import os
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime
import tempfile
import shutil
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, grey
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from PIL import Image as PILImage

# =============================================================================
# Brand Assets
# =============================================================================
APP_DIR = Path(__file__).resolve().parent
LOGO_PATH = APP_DIR / "di_logo.png"
FAVICON_PATH = APP_DIR / "favicon.png"


def _logo_base64() -> str:
    with open(LOGO_PATH, "rb") as logo_file:
        return base64.b64encode(logo_file.read()).decode()


def render_section_header(icon: str, title: str, subtitle: str, *, compact: bool = False) -> None:
    """Render a consistent section heading with icon, title, and description."""
    block_class = "section-block section-block-compact" if compact else "section-block"
    st.markdown(
        f"""
        <div class="{block_class}">
            <div class="section-header">
                <span class="section-header-icon" aria-hidden="true">{icon}</span>
                <div class="section-header-text">
                    <h2 class="section-title">{title}</h2>
                    <p class="section-header-sub">{subtitle}</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render the site-wide page footer."""
    year = datetime.now().year
    st.markdown(
        f"""
        <footer class="app-footer">
            <div class="app-footer-inner">
                <div class="app-footer-brand">
                    <img src="data:image/png;base64,{_logo_base64()}" alt="DataInsight logo" class="app-footer-logo"/>
                    <span class="app-footer-name">DataInsight</span>
                </div>
                <p class="app-footer-copy">&copy; {year} DataInsight</p>
                <p class="app-footer-meta">Powered by Google Gemini</p>
            </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# Page Config (MUST BE FIRST)
# =============================================================================
st.set_page_config(
    page_title="AI Data Analyst | DataInsight",
    page_icon=str(FAVICON_PATH),
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# Custom Theme & Styling
# =============================================================================
primary_yellow = "#FFC107"
primary_black = "#121212"
primary_white = "#FFFFFF"
light_gray = "#F5F5F5"
border_color = "#E0E0E0"
accent_cream = "#FFFBF0"
accent_warm = "#FFF8E1"

custom_css = f"""
<style>
    /* Primary Colors */
    :root {{
        --primary-yellow: {primary_yellow};
        --primary-yellow-light: #FFD54F;
        --primary-yellow-dark: #FFB300;
        --primary-black: {primary_black};
        --primary-white: {primary_white};
        --light-gray: {light_gray};
        --accent-cream: {accent_cream};
        --accent-warm: {accent_warm};
        --shadow-sm: 0 1px 3px rgba(18, 18, 18, 0.05);
        --shadow-md: 0 4px 20px rgba(18, 18, 18, 0.07);
        --shadow-lg: 0 12px 40px rgba(18, 18, 18, 0.1);
        --shadow-yellow: 0 6px 28px rgba(255, 193, 7, 0.16);
        --radius-sm: 10px;
        --radius-md: 14px;
        --radius-lg: 18px;
        --main-content-width: 92%;
        --main-content-padding-x: 1.25rem;
        --body-card-gap: 1.25rem;
        --body-card-gap-lg: 1.75rem;
    }}

    /* Main Background */
    .stApp {{
        background-color: #ECEEF2;
    }}

    footer[data-testid="stFooter"] {{
        visibility: hidden;
        height: 0;
    }}

    header[data-testid="stHeader"] {{
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid {border_color};
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: {primary_black};
    }}

    [data-testid="stSidebar"] * {{
        color: {primary_white} !important;
    }}

    /* Headers */
    h1, h2, h3 {{
        color: {primary_black} !important;
        font-weight: 700;
    }}

    /* Main Title */
    .main-title {{
        color: {primary_black};
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }}

    .subtitle {{
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }}

    /* Buttons */
    .stButton > button {{
        background-color: {primary_yellow} !important;
        color: {primary_black} !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 2rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }}

    .stButton > button:hover {{
        background-color: #FFB300 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3) !important;
    }}

    /* Text Area */
    .stTextArea textarea {{
        border: 2px solid {primary_yellow} !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
    }}

    .stTextArea textarea:focus {{
        border-color: {primary_black} !important;
        box-shadow: 0 0 0 3px rgba(255, 193, 7, 0.1) !important;
    }}

    /* File Uploader */
    .stFileUploader {{
        border: 2px dashed {primary_yellow} !important;
        border-radius: 8px !important;
        padding: 1.5rem !important;
    }}

    /* Containers & Cards (sidebar metric-card unchanged) */
    section.main .card,
    [data-testid="stMain"] .card {{
        background: linear-gradient(180deg, {primary_white} 0%, #FDFDFB 100%);
        border: 1px solid rgba(18, 18, 18, 0.07);
        border-left: 4px solid {primary_yellow};
        padding: 1.5rem 1.75rem;
        border-radius: var(--radius-md);
        margin: 0;
        box-shadow: var(--shadow-sm), var(--shadow-md);
        line-height: 1.65;
        font-size: 0.95rem;
        color: #444;
        transition: box-shadow 0.25s ease, border-color 0.25s ease;
    }}

    section.main .card:hover,
    [data-testid="stMain"] .card:hover {{
        border-left-color: #FFB300;
        box-shadow: var(--shadow-yellow), var(--shadow-sm);
    }}

    .card {{
        background-color: {primary_white};
        border: 1px solid {border_color};
        border-left: 4px solid {primary_yellow};
        padding: 1.5rem 1.75rem;
        border-radius: 12px;
        margin: 0;
        box-shadow: 0 2px 8px rgba(18, 18, 18, 0.04);
        line-height: 1.65;
        font-size: 0.95rem;
        color: #444;
    }}

    .card strong {{
        color: {primary_black};
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        display: block;
        margin-bottom: 0.85rem;
    }}

    /* Metric Boxes (sidebar dataset info) */
    .metric-cards-stack {{
        display: flex;
        flex-direction: column;
        gap: 0.65rem;
    }}

    .metric-card {{
        background: linear-gradient(135deg, {primary_yellow}15 0%, transparent 100%);
        border: 2px solid {primary_yellow};
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }}

    .metric-label {{
        color: #666;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .metric-value {{
        color: {primary_black};
        font-size: 2rem;
        font-weight: 700;
        margin-top: 0.5rem;
    }}

    /* ── Main content area only ── */
    section.main, [data-testid="stMain"] {{
        background:
            radial-gradient(ellipse 80% 50% at 50% -10%, rgba(255, 193, 7, 0.09) 0%, transparent 55%),
            radial-gradient(ellipse 60% 40% at 100% 50%, rgba(18, 18, 18, 0.03) 0%, transparent 50%),
            linear-gradient(165deg, #E8EBF0 0%, #F0F2F5 45%, #F4F2EC 100%);
    }}

    section.main .block-container, [data-testid="stMain"] .block-container {{
        max-width: var(--main-content-width) !important;
        width: var(--main-content-width) !important;
        padding-top: 2.5rem;
        padding-bottom: 0;
        padding-left: var(--main-content-padding-x);
        padding-right: var(--main-content-padding-x);
    }}

    section.main [data-testid="stVerticalBlock"],
    [data-testid="stMain"] [data-testid="stVerticalBlock"] {{
        max-width: 100%;
    }}

    section.main .block-container > div > [data-testid="stVerticalBlock"]:not(:has(.app-footer)),
    [data-testid="stMain"] .block-container > div > [data-testid="stVerticalBlock"]:not(:has(.app-footer)) {{
        gap: var(--body-card-gap) !important;
    }}

    section.main [data-testid="column"] [data-testid="stVerticalBlock"],
    [data-testid="stMain"] [data-testid="column"] [data-testid="stVerticalBlock"] {{
        gap: 1rem !important;
    }}

    section.main [data-testid="stHorizontalBlock"],
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] {{
        max-width: 100%;
        width: 100%;
    }}

    section.main [data-testid="stHorizontalBlock"]:has(.dash-stat-card),
    section.main [data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]),
    [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(.dash-stat-card),
    [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]) {{
        gap: 1rem !important;
        margin-bottom: var(--body-card-gap) !important;
    }}

    section.main .content-panel,
    section.main .sql-panel,
    section.main .insights-panel,
    section.main .chart-container,
    section.main .results-summary-bar,
    section.main .dash-stat-card,
    [data-testid="stMain"] .content-panel,
    [data-testid="stMain"] .sql-panel,
    [data-testid="stMain"] .insights-panel,
    [data-testid="stMain"] .chart-container,
    [data-testid="stMain"] .results-summary-bar,
    [data-testid="stMain"] .dash-stat-card {{
        width: 100%;
        box-sizing: border-box;
    }}

    section.main .insights-panel,
    [data-testid="stMain"] .insights-panel {{
        max-width: 100%;
    }}

    section.main [data-testid="stPlotlyChart"],
    section.main [data-testid="stDataFrame"],
    section.main .stCode,
    [data-testid="stMain"] [data-testid="stPlotlyChart"],
    [data-testid="stMain"] [data-testid="stDataFrame"],
    [data-testid="stMain"] .stCode {{
        width: 100% !important;
        max-width: 100% !important;
    }}

    div[data-testid="stMarkdown"]:has(.app-hero) {{
        width: 100%;
        display: flex;
        justify-content: center;
        margin-top: 1.5rem;
    }}

    section.main h1, section.main h2, section.main h3,
    [data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3 {{
        letter-spacing: -0.02em;
    }}

    /* Content panels */
    .content-panel {{
        background: linear-gradient(180deg, {primary_white} 0%, #FDFDFB 100%);
        border: 1px solid rgba(18, 18, 18, 0.07);
        border-radius: var(--radius-lg);
        padding: 1.75rem 2rem;
        margin: 0;
        box-shadow: var(--shadow-sm), var(--shadow-md);
        transition: box-shadow 0.28s ease, border-color 0.28s ease, transform 0.28s ease;
        position: relative;
        overflow: hidden;
    }}

    .content-panel::before {{
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 120px;
        height: 120px;
        background: radial-gradient(circle, rgba(255, 193, 7, 0.06) 0%, transparent 70%);
        pointer-events: none;
    }}

    section.main .content-panel:hover,
    [data-testid="stMain"] .content-panel:hover {{
        border-color: rgba(255, 193, 7, 0.28);
        box-shadow: var(--shadow-sm), var(--shadow-lg);
    }}

    .content-panel-compact {{
        padding: 1.25rem 1.5rem;
    }}

    .content-panel-accent {{
        border-top: 3px solid {primary_yellow};
        background: linear-gradient(180deg, {accent_cream} 0%, {primary_white} 28%, #FDFDFB 100%);
        margin-top: var(--body-card-gap-lg);
    }}

    section.main div[data-testid="stMarkdown"]:has(.content-panel-accent),
    section.main div[data-testid="stElementContainer"]:has(.content-panel-accent),
    [data-testid="stMain"] div[data-testid="stMarkdown"]:has(.content-panel-accent),
    [data-testid="stMain"] div[data-testid="stElementContainer"]:has(.content-panel-accent) {{
        margin-bottom: var(--body-card-gap-lg) !important;
    }}

    .content-panel-accent::after {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, {primary_yellow}, {primary_black} 50%, {primary_yellow});
        opacity: 0.85;
    }}

    .content-panel:empty {{
        display: none;
        padding: 0;
        margin: 0;
        border: none;
        box-shadow: none;
    }}

    .panel-header {{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1.25rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(18, 18, 18, 0.06);
        background: linear-gradient(90deg, rgba(255, 193, 7, 0.04) 0%, transparent 60%);
        margin-left: -0.5rem;
        margin-right: -0.5rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
        border-radius: var(--radius-sm);
    }}

    .panel-header-text {{
        flex: 1;
    }}

    .panel-eyebrow {{
        color: {primary_yellow};
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 0 0 0.35rem 0;
    }}

    .panel-title {{
        color: {primary_black};
        font-size: 1.1rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.3;
    }}

    .panel-desc {{
        color: #777;
        font-size: 0.875rem;
        margin: 0.35rem 0 0;
        line-height: 1.5;
    }}

    .panel-badge {{
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.85rem;
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.18) 0%, rgba(255, 193, 7, 0.08) 100%);
        color: {primary_black};
        border: 1px solid rgba(255, 193, 7, 0.4);
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        white-space: nowrap;
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(255, 193, 7, 0.12);
        letter-spacing: 0.03em;
    }}

    /* Section Headers */
    .section-block {{
        margin: 2.75rem 0 0 0;
        padding-bottom: 0.25rem;
        position: relative;
    }}

    .section-block::after {{
        content: '';
        display: block;
        height: 2px;
        margin-top: 0.85rem;
        background: linear-gradient(90deg, {primary_yellow} 0%, rgba(255, 193, 7, 0.35) 35%, transparent 75%);
        border-radius: 2px;
    }}

    .section-block-compact {{
        margin-top: 1.5rem;
    }}

    .section-block-compact::after {{
        margin-top: 0.65rem;
        max-width: 12rem;
    }}

    .section-header {{
        display: flex;
        align-items: flex-start;
        gap: 0.85rem;
        margin: 0;
        padding: 0.65rem 0.85rem;
        background: linear-gradient(90deg, rgba(255, 255, 255, 0.7) 0%, rgba(255, 255, 255, 0.35) 100%);
        border: 1px solid rgba(18, 18, 18, 0.05);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
    }}

    .section-header-icon {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.65rem;
        height: 2.65rem;
        background: linear-gradient(145deg, rgba(255, 193, 7, 0.22) 0%, rgba(255, 193, 7, 0.08) 100%);
        border: 1px solid rgba(255, 193, 7, 0.35);
        border-radius: 12px;
        font-size: 1.15rem;
        flex-shrink: 0;
        line-height: 1;
        box-shadow: 0 3px 10px rgba(255, 193, 7, 0.15);
    }}

    .section-header-text {{
        flex: 1;
        min-width: 0;
        padding-top: 0.1rem;
    }}

    .section-title {{
        color: {primary_black} !important;
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        margin: 0 0 0.3rem 0 !important;
        padding: 0 !important;
        letter-spacing: -0.02em !important;
        line-height: 1.3 !important;
        border: none !important;
    }}

    .section-header-sub {{
        color: #777;
        font-size: 0.875rem;
        font-weight: 400;
        margin: 0;
        line-height: 1.5;
    }}

    /* Dashboard stat cards (main body only) */
    .dash-stat-card {{
        background: linear-gradient(160deg, {primary_white} 0%, #FEFDF9 55%, {accent_warm} 100%);
        border: 1px solid rgba(18, 18, 18, 0.07);
        border-radius: var(--radius-md);
        padding: 1.25rem 1.35rem;
        text-align: left;
        box-shadow: var(--shadow-sm), var(--shadow-md);
        transition: box-shadow 0.25s ease, border-color 0.25s ease, transform 0.25s ease;
        height: 100%;
        position: relative;
        overflow: hidden;
    }}

    .dash-stat-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, {primary_yellow}, {primary_black});
        opacity: 0.75;
    }}

    .dash-stat-card:hover {{
        border-color: rgba(255, 193, 7, 0.5);
        box-shadow: var(--shadow-yellow), var(--shadow-md);
        transform: translateY(-3px);
    }}

    .dash-stat-card--rows::before {{
        background: linear-gradient(90deg, {primary_yellow}, #FFD54F);
    }}

    .dash-stat-card--cols::before {{
        background: linear-gradient(90deg, {primary_black}, #424242);
    }}

    .dash-stat-label {{
        color: #888;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0;
    }}

    .dash-stat-value {{
        color: {primary_black};
        font-size: 1.65rem;
        font-weight: 800;
        margin: 0.4rem 0 0;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }}

    .dash-stat-icon {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.25rem;
        height: 2.25rem;
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.2) 0%, rgba(255, 193, 7, 0.08) 100%);
        border: 1px solid rgba(255, 193, 7, 0.25);
        border-radius: 9px;
        font-size: 1rem;
        margin-bottom: 0.7rem;
        box-shadow: 0 2px 6px rgba(255, 193, 7, 0.12);
    }}

    /* KPI Cards (main content metrics) */
    section.main div[data-testid="stMetric"],
    [data-testid="stMain"] div[data-testid="stMetric"] {{
        border-radius: var(--radius-md) !important;
        background: linear-gradient(155deg, {primary_white} 0%, #FEFDF8 60%, {accent_warm} 100%) !important;
        border: 1px solid rgba(255, 193, 7, 0.22) !important;
        border-top: 3px solid {primary_yellow} !important;
        box-shadow: var(--shadow-sm), var(--shadow-md) !important;
        padding: 1.2rem 1.35rem !important;
        margin-bottom: 0 !important;
        min-height: 112px;
        transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.25s ease !important;
        position: relative;
        overflow: hidden;
    }}

    section.main div[data-testid="stMetric"]::after,
    [data-testid="stMain"] div[data-testid="stMetric"]::after {{
        content: '';
        position: absolute;
        bottom: -20px;
        right: -20px;
        width: 80px;
        height: 80px;
        background: radial-gradient(circle, rgba(255, 193, 7, 0.08) 0%, transparent 70%);
        pointer-events: none;
    }}

    section.main div[data-testid="stMetric"]:hover,
    [data-testid="stMain"] div[data-testid="stMetric"]:hover {{
        border-color: rgba(255, 193, 7, 0.55) !important;
        box-shadow: var(--shadow-yellow), var(--shadow-md) !important;
        transform: translateY(-2px) !important;
    }}

    section.main [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4n+2) div[data-testid="stMetric"],
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4n+2) div[data-testid="stMetric"] {{
        border-top-color: {primary_black} !important;
        background: linear-gradient(155deg, {primary_white} 0%, #FAFAFA 60%, #F5F5F5 100%) !important;
    }}

    section.main [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4n+3) div[data-testid="stMetric"],
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4n+3) div[data-testid="stMetric"] {{
        border-top-color: #FFD54F !important;
    }}

    section.main [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4n) div[data-testid="stMetric"],
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4n) div[data-testid="stMetric"] {{
        border-top-color: #FFB300 !important;
    }}

    section.main div[data-testid="stMetric"] > div > div:first-child,
    [data-testid="stMain"] div[data-testid="stMetric"] > div > div:first-child {{
        color: #888 !important;
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.07em !important;
        margin-bottom: 0.5rem !important;
    }}

    section.main div[data-testid="stMetric"] > div > div:nth-child(2),
    [data-testid="stMain"] div[data-testid="stMetric"] > div > div:nth-child(2) {{
        color: {primary_black} !important;
        font-size: 1.75rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
    }}

    .kpi-section-label {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 1.5rem 0 1rem 0;
    }}

    .kpi-section-label span {{
        color: #aaa;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}

    /* Workflow steps */
    .app-hero-divider {{
        width: min(100%, 20rem);
        height: 1px;
        margin: 1.75rem 0 0;
        background: linear-gradient(90deg, transparent, rgba(255, 193, 7, 0.5), transparent);
        border: none;
    }}

    .workflow-steps {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0;
        margin-top: 1.25rem;
        width: 100%;
        flex-wrap: nowrap;
    }}

    .workflow-step {{
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        padding: 0.5rem 1rem;
        white-space: nowrap;
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(18, 18, 18, 0.06);
        border-radius: 999px;
        box-shadow: var(--shadow-sm);
        transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }}

    .workflow-step:hover {{
        border-color: rgba(255, 193, 7, 0.4);
        box-shadow: 0 3px 12px rgba(255, 193, 7, 0.12);
    }}

    .workflow-step-num {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.85rem;
        height: 1.85rem;
        background: linear-gradient(145deg, {primary_black} 0%, #2a2a2a 100%);
        color: {primary_yellow};
        border-radius: 50%;
        font-size: 0.72rem;
        font-weight: 800;
        flex-shrink: 0;
        line-height: 1;
        box-shadow: 0 2px 8px rgba(18, 18, 18, 0.2);
        border: 1px solid rgba(255, 193, 7, 0.25);
    }}

    .workflow-step-text {{
        color: #444;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.01em;
    }}

    .workflow-connector {{
        width: 2.25rem;
        height: 2px;
        background: linear-gradient(90deg, rgba(255, 193, 7, 0.2), {primary_yellow}, rgba(255, 193, 7, 0.2));
        flex-shrink: 0;
        align-self: center;
        border-radius: 2px;
    }}

    @media (max-width: 1024px) {{
        :root {{
            --main-content-width: 94%;
            --main-content-padding-x: 1rem;
        }}
    }}

    @media (max-width: 768px) {{
        :root {{
            --main-content-width: 100%;
            --main-content-padding-x: 0.75rem;
        }}

        .content-panel {{
            padding: 1.25rem 1.25rem;
        }}

        .insights-panel {{
            padding: 1.35rem 1.5rem;
        }}

        .chart-container {{
            padding: 1rem 1.1rem 0.65rem;
        }}
    }}

    @media (max-width: 680px) {{
        .workflow-steps {{
            flex-wrap: wrap;
            gap: 0.35rem;
        }}

        .workflow-connector {{
            display: none;
        }}
    }}

    @media (max-width: 480px) {{
        :root {{
            --main-content-padding-x: 0.5rem;
        }}

        .content-panel {{
            padding: 1rem;
        }}

        .dash-stat-card {{
            padding: 1rem 1.1rem;
        }}
    }}

    /* Column list panel */
    .column-list {{
        margin: 0;
        padding: 0;
        list-style: none;
        max-height: 320px;
        overflow-y: auto;
    }}

    .column-list li {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0.35rem;
        border-bottom: 1px solid #F0F0F0;
        color: #444;
        font-size: 0.875rem;
        border-radius: 6px;
        transition: background 0.15s ease, padding-left 0.15s ease;
    }}

    .column-list li:hover {{
        background: rgba(255, 193, 7, 0.06);
        padding-left: 0.55rem;
    }}

    .column-list li:last-child {{
        border-bottom: none;
    }}

    .column-dot {{
        width: 6px;
        height: 6px;
        background: {primary_yellow};
        border-radius: 50%;
        flex-shrink: 0;
    }}

    /* SQL code block panel */
    .sql-panel {{
        background: {primary_black};
        border-radius: 12px;
        padding: 0;
        overflow: hidden;
        border: 1px solid rgba(255, 193, 7, 0.2);
        margin-bottom: 0.75rem;
    }}

    .sql-panel-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.65rem 1.25rem;
        background: rgba(255, 193, 7, 0.08);
        border-bottom: 1px solid rgba(255, 193, 7, 0.15);
    }}

    .sql-panel-title {{
        color: {primary_yellow};
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 0;
    }}

    /* Insights panel */
    .insights-panel {{
        background: linear-gradient(135deg, {accent_cream} 0%, {primary_white} 55%, #FEFEFC 100%);
        border: 1px solid rgba(255, 193, 7, 0.32);
        border-left: 4px solid {primary_yellow};
        border-radius: var(--radius-md);
        padding: 1.85rem 2.1rem;
        margin: 0;
        line-height: 1.75;
        color: #333;
        font-size: 0.95rem;
        box-shadow: var(--shadow-yellow), var(--shadow-sm);
        position: relative;
    }}

    .insights-panel::before {{
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 100px;
        height: 100px;
        background: radial-gradient(circle, rgba(255, 193, 7, 0.1) 0%, transparent 70%);
        pointer-events: none;
    }}

    .insights-panel strong {{
        color: {primary_black};
    }}

    /* Chart container */
    .chart-container {{
        background: linear-gradient(180deg, {primary_white} 0%, #FDFDFB 100%);
        border: 1px solid rgba(18, 18, 18, 0.07);
        border-radius: var(--radius-md);
        padding: 1.35rem 1.6rem 0.75rem;
        box-shadow: var(--shadow-sm), var(--shadow-md);
        margin-bottom: 0;
        position: relative;
        overflow: hidden;
    }}

    .chart-container::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, {primary_yellow}, {primary_black} 60%, transparent);
        opacity: 0.7;
    }}

    section.main [data-testid="stPlotlyChart"],
    [data-testid="stMain"] [data-testid="stPlotlyChart"] {{
        background: {primary_white} !important;
        border: 1px solid rgba(18, 18, 18, 0.06) !important;
        border-radius: var(--radius-md) !important;
        padding: 0.75rem !important;
        box-shadow: var(--shadow-sm) !important;
        overflow: hidden !important;
    }}

    .chart-meta {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.75rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #F0F0F0;
    }}

    .chart-meta-label {{
        color: #888;
        font-size: 0.8rem;
        font-weight: 600;
    }}

    .chart-type-badge {{
        display: inline-flex;
        padding: 0.3rem 0.8rem;
        background: linear-gradient(135deg, {primary_black} 0%, #2d2d2d 100%);
        color: {primary_yellow};
        border-radius: 8px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        border: 1px solid rgba(255, 193, 7, 0.2);
        box-shadow: 0 2px 8px rgba(18, 18, 18, 0.15);
    }}

    /* Results summary bar */
    .results-summary-bar {{
        display: flex;
        align-items: center;
        gap: 1.5rem;
        flex-wrap: wrap;
        padding: 1rem 1.4rem;
        background: linear-gradient(90deg, {accent_cream} 0%, {primary_white} 50%, #FAFAFA 100%);
        border: 1px solid rgba(255, 193, 7, 0.22);
        border-radius: var(--radius-sm);
        margin-bottom: 0;
        box-shadow: var(--shadow-sm);
    }}

    .results-summary-item {{
        display: flex;
        align-items: center;
        gap: 0.4rem;
        color: #666;
        font-size: 0.85rem;
    }}

    .results-summary-item strong {{
        color: {primary_black};
        font-weight: 700;
    }}

    /* Empty state */
    .empty-state {{
        text-align: center;
        padding: 3.5rem 2rem;
        margin: var(--body-card-gap-lg) 0 var(--body-card-gap) 0;
        background: linear-gradient(180deg, {primary_white} 0%, #FDFDFB 60%, {accent_cream} 100%);
        border: 1px solid rgba(18, 18, 18, 0.07);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-md), var(--shadow-lg);
        position: relative;
        overflow: hidden;
    }}

    .empty-state::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, {primary_yellow}, {primary_black}, {primary_yellow});
    }}

    .empty-state-icon {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 4.5rem;
        height: 4.5rem;
        background: rgba(255, 193, 7, 0.12);
        border-radius: 16px;
        font-size: 2rem;
        margin-bottom: 1.25rem;
        border: 1px solid rgba(255, 193, 7, 0.25);
    }}

    .empty-state-title {{
        color: {primary_black};
        font-size: 1.5rem;
        font-weight: 800;
        margin: 0 0 0.5rem;
        letter-spacing: -0.02em;
    }}

    .empty-state-desc {{
        color: #777;
        font-size: 0.95rem;
        line-height: 1.65;
        margin: 0 auto 1.75rem;
        max-width: 28rem;
    }}

    .empty-state-tips {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.85rem;
        text-align: left;
        margin-top: 0.5rem;
    }}

    .empty-state-tip {{
        background: linear-gradient(180deg, {primary_white} 0%, #FAFAFA 100%);
        border: 1px solid rgba(18, 18, 18, 0.06);
        border-radius: var(--radius-sm);
        padding: 1.1rem 1.2rem;
        font-size: 0.82rem;
        color: #666;
        line-height: 1.5;
        transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    }}

    .empty-state-tip:hover {{
        border-color: rgba(255, 193, 7, 0.35);
        box-shadow: 0 4px 14px rgba(255, 193, 7, 0.1);
        transform: translateY(-2px);
    }}

    .empty-state-tip strong {{
        display: block;
        color: {primary_black};
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
    }}

    /* Main-area widget polish */
    section.main [data-testid="stFileUploader"],
    [data-testid="stMain"] [data-testid="stFileUploader"] {{
        background: #FAFAFA !important;
        border: 2px dashed rgba(255, 193, 7, 0.55) !important;
        border-radius: 12px !important;
        padding: 1.25rem !important;
        transition: border-color 0.2s ease, background 0.2s ease !important;
    }}

    section.main [data-testid="stFileUploader"]:hover,
    [data-testid="stMain"] [data-testid="stFileUploader"]:hover {{
        border-color: {primary_yellow} !important;
        background: rgba(255, 193, 7, 0.04) !important;
    }}

    section.main [data-testid="stDataFrame"],
    [data-testid="stMain"] [data-testid="stDataFrame"] {{
        border: 1px solid rgba(18, 18, 18, 0.08) !important;
        border-radius: var(--radius-md) !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-sm), var(--shadow-md) !important;
        background: {primary_white} !important;
    }}

    section.main [data-testid="stDataFrame"] [data-testid="stDataFrameResizable"],
    [data-testid="stMain"] [data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {{
        border-radius: var(--radius-md) !important;
    }}

    section.main .stCode, section.main pre,
    [data-testid="stMain"] .stCode, [data-testid="stMain"] pre {{
        border-radius: 0 0 12px 12px !important;
        margin-top: 0 !important;
        border: none !important;
    }}

    /* Action bar */
    .action-bar {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.75rem;
        padding: 0.5rem 0 0.25rem;
    }}

    .action-bar-note {{
        text-align: center;
        color: #aaa;
        font-size: 0.78rem;
        margin-top: 0.5rem;
    }}

    /* Success Messages */
    .stSuccess {{
        background-color: #E8F5E9 !important;
        color: #1B5E20 !important;
        border-left: 4px solid #4CAF50 !important;
    }}

    /* Error Messages */
    .stError {{
        background-color: #FFEBEE !important;
        color: #B71C1C !important;
        border-left: 4px solid #F44336 !important;
    }}

    /* Info Messages */
    .stInfo {{
        background-color: #E3F2FD !important;
        color: #0D47A1 !important;
        border-left: 4px solid {primary_yellow} !important;
    }}

    /* Warning Messages */
    .stWarning {{
        background-color: #FFF3E0 !important;
        color: #E65100 !important;
        border-left: 4px solid #FF9800 !important;
    }}

    /* Code Block */
    .stCode {{
        background-color: {primary_black} !important;
        color: {primary_yellow} !important;
        border-radius: 8px !important;
    }}

    /* Divider */
    .divider {{
        height: 2px;
        background: linear-gradient(to right, {primary_yellow}, transparent);
        margin: 2rem 0;
    }}

    /* DataFrames */
    [data-testid="stDataFrame"] {{
        border-radius: 8px !important;
    }}

    /* Sidebar History */
    .history-item {{
        background-color: rgba(255, 193, 7, 0.1);
        border-left: 3px solid {primary_yellow};
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }}

    /* Branding */
    [data-testid="stSidebar"] [data-testid="stLogo"] {{
        padding-bottom: 0.25rem;
    }}

    .sidebar-brand {{
        margin: 0.5rem 0 0;
    }}

    .brand-sidebar-name {{
        color: {primary_yellow};
        font-size: 1.15rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        margin: 0;
        line-height: 1.3;
    }}

    .brand-sidebar-tagline {{
        color: #888;
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 0.35rem 0 0;
    }}

    .sidebar-divider {{
        height: 1px;
        background: rgba(255, 193, 7, 0.25);
        margin: 1.25rem 0;
    }}

    .app-hero {{
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center !important;
        padding: 2.75rem 2.25rem 2.25rem;
        width: 100%;
        max-width: 100%;
        margin: 0.75rem auto var(--body-card-gap);
        background: linear-gradient(165deg, {primary_white} 0%, #FDFDFB 45%, {accent_cream} 100%);
        border: 1px solid rgba(18, 18, 18, 0.07);
        border-radius: 22px;
        box-shadow: var(--shadow-sm), var(--shadow-lg);
        position: relative;
        overflow: hidden;
        box-sizing: border-box;
    }}

    .app-hero::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, {primary_yellow}, {primary_black} 45%, {primary_yellow});
    }}

    .app-hero::after {{
        content: '';
        position: absolute;
        bottom: -60px;
        left: 50%;
        transform: translateX(-50%);
        width: 280px;
        height: 120px;
        background: radial-gradient(ellipse, rgba(255, 193, 7, 0.12) 0%, transparent 70%);
        pointer-events: none;
    }}

    [data-testid="stMarkdown"] .app-hero,
    [data-testid="stMarkdown"] .app-hero * {{
        text-align: center !important;
        letter-spacing: normal !important;
        word-spacing: normal !important;
        text-justify: auto !important;
    }}

    .app-hero-logo {{
        display: flex;
        align-items: center;
        justify-content: center;
        background: {primary_black};
        border-radius: 18px;
        padding: 14px;
        margin: 0 auto 1.35rem;
        box-shadow: 0 8px 28px rgba(18, 18, 18, 0.12);
        border: 1px solid rgba(255, 193, 7, 0.15);
    }}

    .app-hero-logo img {{
        display: block;
        width: 88px;
        height: 88px;
        object-fit: contain;
    }}

    .app-hero-title {{
        color: {primary_black} !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: clamp(1.85rem, 3.5vw, 2.5rem);
        font-weight: 800 !important;
        margin: 0 auto;
        padding: 0;
        width: 100%;
        letter-spacing: -0.025em !important;
        word-spacing: normal !important;
        line-height: 1.15;
        text-align: center !important;
        text-rendering: optimizeLegibility;
        -webkit-font-smoothing: antialiased;
    }}

    .app-hero-subtitle {{
        color: #5c5c5c !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: clamp(0.92rem, 1.8vw, 1.05rem);
        font-weight: 400;
        margin: 0.85rem auto 0;
        max-width: 30rem;
        line-height: 1.6;
        letter-spacing: normal !important;
        word-spacing: normal !important;
        text-align: center !important;
    }}

    .app-hero-badge {{
        display: inline-block;
        margin-top: 1.15rem;
        padding: 0.45rem 1.05rem;
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.18) 0%, rgba(255, 193, 7, 0.08) 100%);
        color: {primary_black} !important;
        border: 1px solid rgba(255, 193, 7, 0.4);
        border-radius: 999px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.03em !important;
        word-spacing: normal !important;
        text-transform: none;
        text-align: center !important;
        box-shadow: 0 2px 10px rgba(255, 193, 7, 0.14);
    }}

    /* Main-area buttons (sidebar unchanged) */
    section.main .stButton > button,
    [data-testid="stMain"] .stButton > button {{
        background: linear-gradient(180deg, {primary_yellow} 0%, #FFB300 100%) !important;
        color: {primary_black} !important;
        border: 1px solid rgba(18, 18, 18, 0.08) !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        padding: 0.65rem 2rem !important;
        font-size: 1rem !important;
        letter-spacing: 0.01em !important;
        box-shadow: 0 2px 8px rgba(255, 193, 7, 0.25), 0 1px 2px rgba(18, 18, 18, 0.06) !important;
        transition: all 0.25s ease !important;
    }}

    section.main .stButton > button:hover,
    [data-testid="stMain"] .stButton > button:hover {{
        background: linear-gradient(180deg, #FFD54F 0%, {primary_yellow} 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-yellow), 0 2px 4px rgba(18, 18, 18, 0.08) !important;
    }}

    section.main .stButton > button:active,
    [data-testid="stMain"] .stButton > button:active {{
        transform: translateY(0) !important;
    }}

    section.main .stDownloadButton > button,
    [data-testid="stMain"] .stDownloadButton > button {{
        background: linear-gradient(180deg, {primary_white} 0%, #F5F5F5 100%) !important;
        color: {primary_black} !important;
        border: 1px solid rgba(18, 18, 18, 0.12) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        box-shadow: var(--shadow-sm) !important;
        transition: all 0.25s ease !important;
    }}

    section.main .stDownloadButton > button:hover,
    [data-testid="stMain"] .stDownloadButton > button:hover {{
        background: linear-gradient(180deg, {accent_cream} 0%, {primary_white} 100%) !important;
        border-color: rgba(255, 193, 7, 0.45) !important;
        box-shadow: var(--shadow-yellow) !important;
        transform: translateY(-1px) !important;
    }}

    /* Main-area form controls */
    section.main .stTextArea textarea,
    [data-testid="stMain"] .stTextArea textarea {{
        background: {primary_white} !important;
        border: 2px solid rgba(255, 193, 7, 0.35) !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: inset 0 1px 3px rgba(18, 18, 18, 0.04) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}

    section.main .stTextArea textarea:focus,
    [data-testid="stMain"] .stTextArea textarea:focus {{
        border-color: {primary_yellow} !important;
        box-shadow: 0 0 0 3px rgba(255, 193, 7, 0.15), inset 0 1px 3px rgba(18, 18, 18, 0.04) !important;
    }}

    section.main [data-baseweb="select"] > div,
    [data-testid="stMain"] [data-baseweb="select"] > div {{
        border-color: rgba(255, 193, 7, 0.35) !important;
        border-radius: var(--radius-sm) !important;
        background: {primary_white} !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}

    section.main [data-baseweb="select"] > div:hover,
    [data-testid="stMain"] [data-baseweb="select"] > div:hover {{
        border-color: {primary_yellow} !important;
    }}

    .query-form-spacer {{
        display: block;
        height: var(--body-card-gap);
        flex-shrink: 0;
    }}

    section.main [data-testid="stExpander"],
    [data-testid="stMain"] [data-testid="stExpander"] {{
        border: 1px solid rgba(18, 18, 18, 0.07) !important;
        border-radius: var(--radius-md) !important;
        background: linear-gradient(180deg, {primary_white}, #FAFAFA) !important;
        box-shadow: var(--shadow-sm) !important;
    }}

    /* SQL panel polish */
    section.main .sql-panel,
    [data-testid="stMain"] .sql-panel {{
        box-shadow: 0 8px 32px rgba(18, 18, 18, 0.18), 0 0 0 1px rgba(255, 193, 7, 0.15);
    }}

    section.main .sql-panel-header,
    [data-testid="stMain"] .sql-panel-header {{
        background: linear-gradient(90deg, rgba(255, 193, 7, 0.12) 0%, rgba(255, 193, 7, 0.04) 100%);
    }}

    /* Alert polish in main area */
    section.main .stSuccess,
    [data-testid="stMain"] .stSuccess {{
        border-radius: var(--radius-sm) !important;
        box-shadow: var(--shadow-sm) !important;
    }}

    section.main .stInfo,
    [data-testid="stMain"] .stInfo {{
        background: linear-gradient(90deg, {accent_cream} 0%, #E3F2FD 100%) !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: var(--shadow-sm) !important;
    }}

    /* Site footer — full-width, flush to viewport bottom */
    div[data-testid="stMarkdown"]:has(.app-footer) {{
        width: 100vw;
        max-width: 100vw;
        margin-left: calc(50% - 50vw);
        margin-right: calc(50% - 50vw);
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }}

    [data-testid="stVerticalBlock"]:has(.app-footer),
    [data-testid="stVerticalBlockBorderWrapper"]:has(.app-footer) {{
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
        gap: 0 !important;
    }}

    .app-footer {{
        margin: 2.5rem 0 0;
        padding: 0;
        width: 100%;
        background: {primary_black};
        border-top: 2px solid {primary_yellow};
        box-sizing: border-box;
    }}

    .app-footer-inner {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
        max-width: 1120px;
        margin: 0 auto;
        padding: 0.65rem 1.5rem;
    }}

    .app-footer-brand {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    .app-footer-logo {{
        width: 22px;
        height: 22px;
        object-fit: contain;
    }}

    .app-footer-name {{
        color: {primary_white};
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.01em;
    }}

    .app-footer-copy,
    .app-footer-meta {{
        color: #757575;
        font-size: 0.72rem;
        margin: 0;
    }}

    @media (max-width: 540px) {{
        .app-footer-inner {{
            flex-direction: column;
            align-items: flex-start;
            padding: 0.65rem 1.25rem;
            gap: 0.35rem;
        }}
    }}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

st.logo(
    str(LOGO_PATH),
    size="large",
    icon_image=str(LOGO_PATH),
)

# =============================================================================
# Load Environment Variables
# =============================================================================
load_dotenv()


def _get_gemini_api_key() -> str:
    """Resolve Gemini API key from Streamlit secrets or environment."""
    try:
        if st.secrets.has_key("GEMINI_API_KEY"):
            return str(st.secrets["GEMINI_API_KEY"]).strip()
    except StreamlitSecretNotFoundError:
        pass

    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        return key

    st.error(
        "Gemini API key not found. Add `GEMINI_API_KEY` to "
        "`.streamlit/secrets.toml` or a `.env` file in the project root."
    )
    st.stop()


genai.configure(api_key=_get_gemini_api_key())

model = genai.GenerativeModel("gemini-2.5-flash")

# =============================================================================
# Session State
# =============================================================================
if "history" not in st.session_state:
    st.session_state.history = []

if "show_results" not in st.session_state:
    st.session_state.show_results = False

if "last_user_question" not in st.session_state:
    st.session_state.last_user_question = None

if "last_sql_query" not in st.session_state:
    st.session_state.last_sql_query = None

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_chart_fig" not in st.session_state:
    st.session_state.last_chart_fig = None

if "last_insights" not in st.session_state:
    st.session_state.last_insights = None

# =============================================================================
# API Error Handling
# =============================================================================
def format_api_error(exception):
    message = str(exception)
    lowered = message.lower()
    if "quota" in lowered or "429" in lowered or "rate limit" in lowered:
        return (
            "Gemini API quota or rate limit error detected. "
            "Please check your Google Cloud billing and quota settings, "
            "or retry again later."
        )
    return message

# =============================================================================
# Visualization Helpers
# =============================================================================
def determine_best_chart_type(data: pd.DataFrame) -> str:
    x_col = data.columns[0]
    y_col = data.columns[1]

    if pd.api.types.is_datetime64_any_dtype(data[x_col]):
        return "Line Chart"

    if pd.api.types.is_numeric_dtype(data[x_col]) and pd.api.types.is_numeric_dtype(data[y_col]):
        return "Scatter Plot"

    return "Bar Chart"


def build_plotly_figure(data: pd.DataFrame, chart_type: str, primary_yellow: str, primary_black: str):
    x_col = data.columns[0]
    y_col = data.columns[1]

    cleaned = data.copy()
    cleaned[y_col] = pd.to_numeric(cleaned[y_col], errors="coerce")
    cleaned = cleaned.dropna(subset=[y_col])

    if cleaned.empty:
        raise ValueError("The selected data cannot be plotted because the value column is not numeric.")

    if chart_type == "Auto":
        chart_type = determine_best_chart_type(cleaned)

    if chart_type == "Bar Chart":
        fig = px.bar(
            cleaned,
            x=x_col,
            y=y_col,
            title=f"{y_col} by {x_col}",
            labels={x_col: x_col, y_col: y_col},
            color_discrete_sequence=[primary_yellow]
        )
    elif chart_type == "Pie Chart":
        fig = px.pie(
            cleaned,
            names=x_col,
            values=y_col,
            title=f"{y_col} distribution by {x_col}",
            color_discrete_sequence=[primary_yellow],
            labels={x_col: x_col, y_col: y_col}
        )
        fig.update_traces(
            textposition='inside',
            textinfo='percent' if len(cleaned) > 8 else 'label+percent',
            insidetextorientation='radial',
            hovertemplate='<b>%{label}</b><br>%{value:,}<br>%{percent}',
            sort=False
        )
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation='v',
                yanchor='middle',
                x=1.02,
                xanchor='left',
                title_text=x_col,
                bordercolor='#E0E0E0',
                borderwidth=1
            )
        )
    elif chart_type == "Line Chart":
        if not (pd.api.types.is_numeric_dtype(cleaned[x_col]) or pd.api.types.is_datetime64_any_dtype(cleaned[x_col])):
            raise ValueError("Line charts require the first column to be numeric or datetime.")

        fig = px.line(
            cleaned,
            x=x_col,
            y=y_col,
            title=f"{y_col} over {x_col}",
            labels={x_col: x_col, y_col: y_col},
            color_discrete_sequence=[primary_yellow]
        )
    elif chart_type == "Scatter Plot":
        if not pd.api.types.is_numeric_dtype(cleaned[x_col]):
            raise ValueError("Scatter plots require both the first and second columns to be numeric.")

        fig = px.scatter(
            cleaned,
            x=x_col,
            y=y_col,
            title=f"{y_col} vs {x_col}",
            labels={x_col: x_col, y_col: y_col},
            color_discrete_sequence=[primary_yellow]
        )
    else:
        raise ValueError("Unsupported chart type selected.")

    fig.update_layout(
        plot_bgcolor="#FEFEFC",
        paper_bgcolor="white",
        font=dict(family="Segoe UI, Arial, sans-serif", size=12, color=primary_black),
        title=dict(
            font=dict(size=17, color=primary_black, family="Segoe UI, Arial, sans-serif"),
            x=0.02,
            xanchor="left",
        ),
        title_font_size=17,
        height=460,
        margin=dict(l=48, r=32, t=56, b=48),
        showlegend=False,
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=primary_black,
            font_color=primary_yellow,
            font_size=12,
            bordercolor=primary_yellow,
        ),
    )
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(18, 18, 18, 0.06)",
        linecolor="rgba(18, 18, 18, 0.12)",
        tickfont=dict(color="#666"),
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(18, 18, 18, 0.06)",
        linecolor="rgba(18, 18, 18, 0.12)",
        tickfont=dict(color="#666"),
    )
    fig.update_traces(
        marker=dict(
            line=dict(color=primary_black, width=0.5),
            opacity=0.92,
        ),
        selector=dict(type="bar"),
    )
    fig.update_traces(
        line=dict(width=2.5, color=primary_yellow),
        marker=dict(size=7, color=primary_yellow, line=dict(color=primary_black, width=1)),
        selector=dict(type="scatter"),
    )

    return fig, chart_type


# =============================================================================
# PDF Report Generation
# =============================================================================
def save_plotly_chart_as_image(fig, width: int = 800, height: int = 450) -> str:
    """
    Convert Plotly figure to temporary image file.
    
    Args:
        fig: Plotly figure object
        width: Image width in pixels
        height: Image height in pixels
    
    Returns:
        Path to temporary image file
    
    Raises:
        RuntimeError: If image conversion fails
    """
    try:
        temp_dir = tempfile.mkdtemp()
        image_path = os.path.join(temp_dir, "chart.png")
        fig.write_image(image_path, width=width, height=height)
        return image_path
    except Exception as e:
        raise RuntimeError(f"Failed to save chart as image: {str(e)}")


def extract_kpi_values(result: pd.DataFrame) -> dict:
    """
    Extract KPI values from query results.
    
    Args:
        result: DataFrame with query results
    
    Returns:
        Dictionary with KPI metrics or empty dict if no numeric data
    """
    kpis = {}
    
    if result is None or result.empty:
        return kpis
    
    numeric_columns = [
        col for col in result.columns
        if pd.api.types.is_numeric_dtype(result[col])
    ]
    
    if not numeric_columns:
        return kpis
    
    numeric_col = numeric_columns[0]
    numeric_series = result[numeric_col].dropna()
    
    if numeric_series.empty:
        return kpis
    
    def format_value(value):
        if pd.isna(value):
            return "N/A"
        if isinstance(value, int):
            return f"{value:,}"
        if isinstance(value, float):
            return f"{value:,.2f}"
        return str(value)
    
    kpis = {
        "Total": format_value(numeric_series.sum()),
        "Average": format_value(numeric_series.mean()),
        "Maximum": format_value(numeric_series.max()),
        "Minimum": format_value(numeric_series.min()),
    }
    
    return kpis


def create_pdf_title_page(story, primary_yellow: str, primary_black: str):
    """
    Add professional title page to PDF.
    
    Args:
        story: List to append PDF elements
        primary_yellow: Primary color hex code
        primary_black: Primary color hex code
    """
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=42,
        textColor=HexColor(primary_black),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    story.append(Spacer(1, 1.2 * inch))
    if LOGO_PATH.exists():
        logo_img = Image(str(LOGO_PATH), width=1.4 * inch, height=1.4 * inch)
        logo_img.hAlign = "CENTER"
        story.append(logo_img)
        story.append(Spacer(1, 0.35 * inch))
    story.append(Paragraph("AI Data Analyst Assistant", title_style))
    story.append(Paragraph("Professional Report", title_style))
    story.append(Spacer(1, 0.5 * inch))
    
    # Subtitle
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=HexColor(primary_yellow),
        alignment=TA_CENTER,
        spaceAfter=24
    )
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
    
    story.append(Spacer(1, 1.5 * inch))
    
    # Footer text
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=11,
        textColor=grey,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    story.append(Paragraph("Transform Your Data Into Actionable Insights", footer_style))
    story.append(PageBreak())


def add_section_header(story, title: str, primary_yellow: str, primary_black: str):
    """
    Add formatted section header to PDF.
    
    Args:
        story: List to append PDF elements
        title: Section title
        primary_yellow: Primary color hex code
        primary_black: Primary color hex code
    """
    styles = getSampleStyleSheet()
    
    header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor(primary_black),
        spaceAfter=12,
        spaceBefore=12,
        borderColor=HexColor(primary_yellow),
        borderPadding=10,
        borderWidth=0,
        fontName='Helvetica-Bold'
    )
    
    story.append(Paragraph(title, header_style))
    story.append(Spacer(1, 0.2 * inch))


def dataframe_to_table(df: pd.DataFrame, max_rows: int = 100) -> Table:
    """
    Convert DataFrame to ReportLab Table with professional styling.
    
    Args:
        df: DataFrame to convert
        max_rows: Maximum rows to include (default 100)
    
    Returns:
        Styled ReportLab Table
    """
    display_df = df.head(max_rows).copy()
    
    # Create data for table
    data = [list(display_df.columns)] + display_df.values.tolist()
    
    # Create table
    table = Table(data, repeatRows=1)
    
    # Style table
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#FFC107')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#121212')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#E0E0E0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F5F5F5')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    
    table.setStyle(table_style)
    return table


def generate_pdf_report(
    user_question: str,
    sql_query: str,
    result: pd.DataFrame,
    insights: str,
    chart_fig: any,
    primary_yellow: str = "#FFC107",
    primary_black: str = "#121212"
) -> bytes:
    """
    Generate professional PDF report with all analysis details.
    
    Args:
        user_question: Original user question
        sql_query: Generated SQL query
        result: Query results as DataFrame
        insights: AI-generated insights text
        chart_fig: Plotly figure object for visualization
        primary_yellow: Primary color hex code
        primary_black: Primary color hex code
    
    Returns:
        PDF file content as bytes
    
    Raises:
        ValueError: If parameters are invalid
        RuntimeError: If PDF generation fails
    """
    try:
        if not user_question or not sql_query or result is None or result.empty:
            raise ValueError("Invalid parameters: all parameters must be provided and non-empty")
        
        # Create in-memory PDF
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Title Page
        create_pdf_title_page(story, primary_yellow, primary_black)
        
        # User Question Section
        add_section_header(story, "📝 Your Question", primary_yellow, primary_black)
        question_style = ParagraphStyle(
            'QuestionText',
            parent=styles['Normal'],
            fontSize=11,
            textColor=black,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=14
        )
        story.append(Paragraph(user_question, question_style))
        story.append(Spacer(1, 0.3 * inch))
        
        # SQL Query Section
        add_section_header(story, "💾 Generated SQL Query", primary_yellow, primary_black)
        sql_style = ParagraphStyle(
            'SQLText',
            parent=styles['Normal'],
            fontSize=9,
            textColor=HexColor('#121212'),
            fontName='Courier',
            alignment=TA_LEFT,
            spaceAfter=12,
            borderColor=HexColor('#E0E0E0'),
            borderPadding=10,
            borderWidth=1,
            backColor=HexColor('#F5F5F5')
        )
        
        # Limit SQL length for display
        sql_display = sql_query[:1000] + ("...[truncated]" if len(sql_query) > 1000 else "")
        story.append(Paragraph(sql_display.replace('\n', '<br/>'), sql_style))
        story.append(Spacer(1, 0.3 * inch))
        
        # Results Summary
        add_section_header(story, "📊 Results Summary", primary_yellow, primary_black)
        summary_style = ParagraphStyle(
            'Summary',
            parent=styles['Normal'],
            fontSize=10,
            textColor=black,
            spaceAfter=12
        )
        total_rows = len(result)
        total_cols = len(result.columns)
        display_rows = min(100, total_rows)
        
        summary_text = f"<b>Total Rows:</b> {total_rows:,} | <b>Columns:</b> {total_cols} | <b>Displayed:</b> {display_rows} rows"
        story.append(Paragraph(summary_text, summary_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Results Table
        try:
            table = dataframe_to_table(result, max_rows=100)
            story.append(KeepTogether(table))
        except Exception as e:
            story.append(Paragraph(f"<i>Unable to render table: {str(e)}</i>", summary_style))
        
        story.append(Spacer(1, 0.3 * inch))
        
        # KPI Summary Section
        kpis = extract_kpi_values(result)
        if kpis:
            add_section_header(story, "📈 KPI Summary", primary_yellow, primary_black)
            
            kpi_data = [["Metric", "Value"]]
            for metric, value in kpis.items():
                kpi_data.append([metric, str(value)])
            
            kpi_table = Table(kpi_data, colWidths=[2 * inch, 2 * inch])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#FFC107')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#121212')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#E0E0E0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F5F5F5')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 0.3 * inch))
        
        # Visualization Section
        try:
            if chart_fig is not None:
                add_section_header(story, "📉 Visualization", primary_yellow, primary_black)
                
                # Save chart temporarily
                chart_image_path = save_plotly_chart_as_image(chart_fig)
                
                try:
                    # Add image with error handling
                    img = Image(chart_image_path, width=6.5 * inch, height=3.5 * inch)
                    story.append(img)
                    story.append(Spacer(1, 0.3 * inch))
                finally:
                    # Cleanup temporary image
                    try:
                        if os.path.exists(chart_image_path):
                            os.remove(chart_image_path)
                        temp_dir = os.path.dirname(chart_image_path)
                        if os.path.exists(temp_dir):
                            shutil.rmtree(temp_dir)
                    except Exception:
                        pass
        except Exception as e:
            story.append(Paragraph(f"<i>Visualization not available: {str(e)}</i>", summary_style))
            story.append(Spacer(1, 0.3 * inch))
        
        # AI Insights Section
        add_section_header(story, "🧠 AI Insights", primary_yellow, primary_black)
        
        if insights and insights.strip():
            insights_style = ParagraphStyle(
                'InsightsText',
                parent=styles['Normal'],
                fontSize=10,
                textColor=black,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                leading=13,
                borderColor=HexColor('#FFC107'),
                borderPadding=12,
                borderWidth=1,
                backColor=HexColor('#FFFAF0')
            )
            story.append(Paragraph(insights.replace('\n', '<br/>'), insights_style))
        else:
            story.append(Paragraph("<i>No AI insights were available for this query.</i>", summary_style))
        
        story.append(Spacer(1, 0.5 * inch))
        
        # Footer
        footer_style = ParagraphStyle(
            'ReportFooter',
            parent=styles['Normal'],
            fontSize=8,
            textColor=grey,
            alignment=TA_CENTER,
            spaceAfter=6
        )
        story.append(Paragraph("—" * 60, footer_style))
        story.append(Paragraph(
            f"Generated by AI Data Analyst | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            footer_style
        ))
        
        # Build PDF
        doc.build(story)
        
        # Return PDF bytes
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    except Exception as e:
        raise RuntimeError(f"PDF generation failed: {str(e)}")


def generate_kpis(result: pd.DataFrame):
    if result is None or result.empty:
        st.info("ℹ️ KPI generation is not available because the query returned no data.", icon="ℹ️")
        return

    numeric_columns = [
        col for col in result.columns
        if pd.api.types.is_numeric_dtype(result[col])
    ]

    if not numeric_columns:
        st.info("ℹ️ No numeric columns were found in the query result, so KPI cards cannot be generated.", icon="ℹ️")
        return

    numeric_col = numeric_columns[0]
    numeric_series = result[numeric_col].dropna()

    if numeric_series.empty:
        st.info("ℹ️ The numeric column contains only null values, so KPI cards cannot be generated.", icon="ℹ️")
        return

    def format_value(value):
        if pd.isna(value):
            return "N/A"
        if isinstance(value, int):
            return f"{value:,}"
        if isinstance(value, float):
            return f"{value:,.2f}"
        return str(value)

    total_value = numeric_series.sum()
    average_value = numeric_series.mean()
    max_value = numeric_series.max()
    min_value = numeric_series.min()

    render_section_header(
        "📈",
        "KPI Dashboard",
        "Key performance indicators computed from your query results",
        compact=True,
    )

    col1, col2, col3, col4 = st.columns(4, gap="medium")
    col1.metric("Total Value", format_value(total_value))
    col2.metric("Average Value", format_value(average_value))
    col3.metric("Maximum Value", format_value(max_value))
    col4.metric("Minimum Value", format_value(min_value))

    categorical_columns = [
        col for col in result.columns
        if col != numeric_col and (
            pd.api.types.is_string_dtype(result[col])
            or pd.api.types.is_categorical_dtype(result[col])
        )
    ]

    if len(categorical_columns) == 1 and len(numeric_columns) == 1:
        category_col = categorical_columns[0]
        category_data = result[[category_col, numeric_col]].dropna()

        if not category_data.empty:
            grouped = category_data.groupby(category_col, dropna=False)[numeric_col].sum()
            if not grouped.empty:
                top_category = grouped.idxmax()
                lowest_category = grouped.idxmin()

                col5, col6, col7, col8 = st.columns(4, gap="medium")
                col5.metric("Top Category", str(top_category))
                col6.metric("Lowest Category", str(lowest_category))

    # If categorical KPI cards are not applicable, do not display additional metrics.

# =============================================================================
# Sidebar Configuration
# =============================================================================
with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-brand">
            <p class="brand-sidebar-name">AI Data Analyst</p>
            <p class="brand-sidebar-tagline">DataInsight Platform</p>
        </div>
        <div class="sidebar-divider"></div>
        """,
        unsafe_allow_html=True,
    )
    
    # About Section
    st.markdown(
        f"<p style='color: #ccc; font-size: 0.9rem; line-height: 1.6;'>"
        "Transform your data into actionable insights with the power of AI. "
        "Upload your dataset (CSV or Excel) and ask questions in plain English.</p>",
        unsafe_allow_html=True
    )
    
    st.markdown("<div style='height: 1px; background: rgba(255,193,7,0.3); margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
    
    # Query History
    st.markdown(
        f"<h3 style='color: {primary_yellow}; font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem;'>📝 Query History</h3>",
        unsafe_allow_html=True
    )
    
    if st.session_state.history:
        for idx, item in enumerate(st.session_state.history, 1):
            st.markdown(
                f"<div class='history-item'><strong>Q{idx}:</strong> {item[:50]}{'...' if len(item) > 50 else ''}</div>",
                unsafe_allow_html=True
            )
        
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.markdown(
            f"<p style='color: #999; font-size: 0.9rem; text-align: center; padding: 1rem 0;'>No queries yet</p>",
            unsafe_allow_html=True
        )
    
    st.markdown("<div style='height: 1px; background: rgba(255,193,7,0.3); margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
    
    # Dataset Summary (will be populated after upload)
    st.markdown(
        f"<h3 style='color: {primary_yellow}; font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem;'>📊 Dataset Info</h3>",
        unsafe_allow_html=True
    )
    dataset_placeholder = st.empty()

# =============================================================================
# Main Page Header
# =============================================================================
st.markdown(
    f"""
    <div class="app-hero">
        <div class="app-hero-logo">
            <img src="data:image/png;base64,{_logo_base64()}" alt="DataInsight logo"/>
        </div>
        <div class="app-hero-title">AI Data Analyst</div>
        <p class="app-hero-subtitle">Transform raw data into SQL queries, visualizations, and actionable business insights — all from plain English questions.</p>
        <span class="app-hero-badge">Powered by DataInsight</span>
        <div class="app-hero-divider" role="presentation"></div>
        <div class="workflow-steps">
            <div class="workflow-step">
                <span class="workflow-step-num">1</span>
                <span class="workflow-step-text">Upload Data</span>
            </div>
            <div class="workflow-connector" role="presentation"></div>
            <div class="workflow-step">
                <span class="workflow-step-num">2</span>
                <span class="workflow-step-text">Ask a Question</span>
            </div>
            <div class="workflow-connector" role="presentation"></div>
            <div class="workflow-step">
                <span class="workflow-step-num">3</span>
                <span class="workflow-step-text">Get Insights</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# Upload CSV Section
# =============================================================================
render_section_header(
    "📤",
    "Upload Your Data",
    "Import a CSV or Excel file to begin your analysis session",
)

st.markdown(
    """
    <div class="content-panel content-panel-accent">
        <div class="panel-header" style="margin-bottom:0;padding-bottom:0;border-bottom:none;">
            <div class="panel-header-text">
                <p class="panel-eyebrow">Data Source</p>
                <p class="panel-title">Select your dataset</p>
                <p class="panel-desc">Supported formats: CSV, XLSX, XLS — up to standard file sizes</p>
            </div>
            <span class="panel-badge">Step 1 of 3</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx", "xls"],
    help="Select a CSV or Excel (.xlsx / .xls) file to analyze with AI"
)

if uploaded_file is not None:
    # Basic validations
    if hasattr(uploaded_file, "size") and uploaded_file.size == 0:
        st.error("❌ The uploaded file is empty. Please upload a non-empty file.", icon="❌")
        st.stop()

    filename = uploaded_file.name.lower() if hasattr(uploaded_file, "name") else ""

    try:
        raw_bytes = uploaded_file.read()
    except Exception as e:
        st.error(f"❌ Failed to read the uploaded file: {str(e)}", icon="❌")
        st.stop()

    # Try to load based on extension
    df = None
    file_size_kb = (len(raw_bytes) / 1024) if raw_bytes is not None else 0

    try:
        if filename.endswith(".csv") or (not filename and uploaded_file.type == "text/csv"):
            try:
                df = pd.read_csv(BytesIO(raw_bytes))
            except pd.errors.EmptyDataError:
                st.error("❌ The CSV file is empty or contains no data.", icon="❌")
                st.stop()
            except Exception as e:
                st.error(f"❌ Failed to parse CSV: {str(e)}", icon="❌")
                st.stop()

        elif filename.endswith(('.xls', '.xlsx')) or uploaded_file.type in ("application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
            # Determine explicit Excel engine by extension
            engine = None
            if filename.endswith('.xlsx'):
                engine = 'openpyxl'
            elif filename.endswith('.xls'):
                engine = 'xlrd'

            try:
                excel_io = BytesIO(raw_bytes)
                xls = pd.ExcelFile(excel_io, engine=engine) if engine else pd.ExcelFile(excel_io)
            except ImportError as e:
                missing = 'openpyxl' if filename.endswith('.xlsx') else 'xlrd'
                st.error(
                    f"❌ Excel engine '{missing}' is not installed. Install it with `pip install {missing}` and retry.",
                    icon="❌"
                )
                st.stop()
            except Exception as e:
                st.error(
                    "❌ The uploaded Excel file appears to be corrupted or in an unsupported format. "
                    f"({str(e)})",
                    icon="❌"
                )
                st.stop()

            # If multiple sheets, allow user to choose
            sheet_names = xls.sheet_names if hasattr(xls, 'sheet_names') else []

            if not sheet_names:
                st.error("❌ No sheets were found in the Excel workbook.", icon="❌")
                st.stop()

            selected_sheet = sheet_names[0]
            if len(sheet_names) > 1:
                selected_sheet = st.selectbox("Select sheet to load", sheet_names)

            try:
                df = pd.read_excel(BytesIO(raw_bytes), sheet_name=selected_sheet, engine=engine)
            except pd.errors.EmptyDataError:
                st.error("❌ The selected Excel sheet is empty.", icon="❌")
                st.stop()
            except ImportError as e:
                missing = 'openpyxl' if filename.endswith('.xlsx') else 'xlrd'
                st.error(
                    f"❌ Excel engine '{missing}' is not installed. Install it with `pip install {missing}` and retry.",
                    icon="❌"
                )
                st.stop()
            except Exception as e:
                st.error(f"❌ Failed to parse Excel file: {str(e)}", icon="❌")
                st.stop()
        else:
            st.error("❌ Unsupported file format. Please upload a CSV or Excel file.", icon="❌")
            st.stop()

    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}", icon="❌")
        st.stop()

    # Final checks
    if df is None:
        st.error("❌ Unable to load the dataset. Please check the file and try again.", icon="❌")
        st.stop()

    if df.empty:
        st.error("❌ The dataset contains no rows. Please upload a file with data.", icon="❌")
        st.stop()

    # Dataset Summary
    with dataset_placeholder.container():
        st.markdown(
            f"""
            <div class="metric-cards-stack">
                <div class="metric-card">
                    <div class="metric-label">Total Rows</div>
                    <div class="metric-value">{df.shape[0]:,}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Columns</div>
                    <div class="metric-value">{df.shape[1]}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Data Size</div>
                    <div class="metric-value">{file_size_kb:.1f} KB</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Save to SQLite (preserve existing behavior)
    try:
        conn = sqlite3.connect("database.db")
        df.to_sql(
            "uploaded_data",
            conn,
            if_exists="replace",
            index=False
        )
        conn.close()
    except Exception as e:
        st.error(f"❌ Failed to save dataset to local database: {str(e)}", icon="❌")
        st.stop()

    st.success("✅ Dataset uploaded successfully! Ready to analyze.", icon="✅")

    # Preview Section
    render_section_header(
        "👁️",
        "Data Preview",
        "Review your dataset structure and sample records before querying",
    )

    col1, col2 = st.columns([2.2, 1], gap="large")
    with col1:
        st.markdown(
            """
            <div class="content-panel content-panel-compact" style="margin-bottom:0;">
                <div class="panel-header" style="margin-bottom:0.75rem;padding-bottom:0.75rem;">
                    <div class="panel-header-text">
                        <p class="panel-eyebrow">Preview</p>
                        <p class="panel-title">First 10 rows</p>
                    </div>
                    <span class="panel-badge">Sample</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(
            df.head(10),
            hide_index=True,
            use_container_width=True
        )
    with col2:
        column_items = "".join(
            f"<li><span class='column-dot'></span>{col}</li>"
            for col in df.columns
        )
        st.markdown(
            f"""
            <div class="card" style="height:100%;">
                <strong>Schema · {len(df.columns)} columns</strong>
                <ul class="column-list">{column_items}</ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Question Input Section
    render_section_header(
        "❓",
        "Ask a Question",
        "Describe what you want to know — AI will generate and run the SQL for you",
    )

    st.markdown(
        """
        <div class="content-panel content-panel-accent">
            <div class="panel-header" style="margin-bottom:0;padding-bottom:0;border-bottom:none;">
                <div class="panel-header-text">
                    <p class="panel-eyebrow">Natural Language Query</p>
                    <p class="panel-title">What would you like to analyze?</p>
                    <p class="panel-desc">Be specific for best results — mention columns, filters, aggregations, or limits.</p>
                </div>
                <span class="panel-badge">Step 2 of 3</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_input = st.text_area(
        "What would you like to know about your data?",
        placeholder="Example: Show top 5 customers by sales\nExample: Calculate average salary by department\nExample: Find total revenue this year",
        height=120,
        label_visibility="collapsed"
    )

    chart_type = st.selectbox(
        "Choose chart type",
        ["Auto", "Bar Chart", "Pie Chart", "Line Chart", "Scatter Plot"],
        index=0,
        help="Auto chooses the best chart for the result, or select the type you want explicitly."
    )

    st.markdown('<div class="query-form-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)

    # Generate Button with formatting
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        if st.button("🚀 Generate Insights", use_container_width=True, key="generate_btn"):

            if user_input.strip() == "":
                st.warning("⚠️ Please enter a question to analyze.", icon="⚠️")
                st.stop()

            with st.spinner("🔄 Analyzing your data..."):
                st.session_state.history.append(user_input)
                st.session_state.show_results = True

                columns = ", ".join(df.columns)

                prompt = f"""
You are an expert SQL analyst. Generate a SQL query to answer the following question.

Database Table:
uploaded_data

Columns:
{columns}

Rules:
1. Return ONLY the SQL query.
2. No explanation, no markdown formatting.
3. No backticks or code fences.
4. Use only the 'uploaded_data' table.
5. Always use aliases for aggregate functions (e.g., COUNT(*) AS total_count).
6. Write clean, optimized SQL.

User Question:
{user_input}
"""

                try:

                    # Generate SQL
                    response = model.generate_content(prompt)

                    sql_query = response.text.strip()

                    # Safety Checks
                    if sql_query.upper().count("SELECT") > 1:
                        st.error("❌ Please ask only one question at a time.", icon="❌")
                        st.stop()

                    if not sql_query.upper().startswith("SELECT"):
                        st.error("❌ Only SELECT queries are allowed for security reasons.", icon="❌")
                        st.stop()

                    # Display SQL Code
                    render_section_header(
                        "💾",
                        "Generated SQL",
                        "AI-generated query executed against your uploaded dataset",
                    )
                    st.markdown(
                        """
                        <div class="sql-panel">
                            <div class="sql-panel-header">
                                <p class="sql-panel-title">SQL Query</p>
                                <span class="panel-badge" style="background:rgba(255,193,7,0.15);border-color:rgba(255,193,7,0.3);">SELECT only</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.code(sql_query, language="sql")

                    # Execute Query
                    conn = sqlite3.connect("database.db")

                    result = pd.read_sql_query(sql_query, conn)

                    conn.close()

                    # Display Results
                    render_section_header(
                        "📋",
                        "Results",
                        "Query output returned from your dataset",
                    )

                    if result.empty:
                        st.info("ℹ️ The query returned no results. Try modifying your question.", icon="ℹ️")
                    else:
                        st.markdown(
                            f"""
                            <div class="results-summary-bar">
                                <div class="results-summary-item">📊 <strong>{len(result):,}</strong> rows returned</div>
                                <div class="results-summary-item">📑 <strong>{len(result.columns)}</strong> columns</div>
                                <div class="results-summary-item">✅ Query executed successfully</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.dataframe(
                            result,
                            hide_index=True,
                            use_container_width=True
                        )

                        generate_kpis(result)

                        st.markdown(
                            """
                            <div class="panel-header" style="margin-top:1.5rem;margin-bottom:1rem;">
                                <div class="panel-header-text">
                                    <p class="panel-eyebrow">Export</p>
                                    <p class="panel-title">Download your results</p>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        col1, col2, col3 = st.columns(3, gap="medium")
                        with col1:
                            st.markdown(
                                f"""
                                <div class="dash-stat-card dash-stat-card--rows">
                                    <div class="dash-stat-icon">📊</div>
                                    <p class="dash-stat-label">Rows</p>
                                    <p class="dash-stat-value">{len(result):,}</p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        with col2:
                            st.markdown(
                                f"""
                                <div class="dash-stat-card dash-stat-card--cols">
                                    <div class="dash-stat-icon">📑</div>
                                    <p class="dash-stat-label">Columns</p>
                                    <p class="dash-stat-value">{len(result.columns)}</p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        with col3:
                            csv = result.to_csv(index=False)
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv,
                                file_name="results.csv",
                                mime="text/csv",
                                use_container_width=True
                            )

                        # PDF Report Button (add a new row for PDF)
                        col_pdf1, col_pdf2, col_pdf3 = st.columns(3)
                        
                        with col_pdf2:
                            try:
                                pdf_bytes = generate_pdf_report(
                                    user_question=user_input,
                                    sql_query=sql_query,
                                    result=result,
                                    insights=st.session_state.get("last_insights", ""),
                                    chart_fig=st.session_state.get("last_chart_fig"),
                                    primary_yellow=primary_yellow,
                                    primary_black=primary_black
                                )
                                
                                st.download_button(
                                    label="📄 Download PDF Report",
                                    data=pdf_bytes,
                                    file_name=f"AI_Data_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            except Exception as e:
                                st.warning(f"⚠️ PDF generation unavailable: {str(e)[:100]}", icon="⚠️")

                        # Visualization
                        render_section_header(
                            "📊",
                            "Visualization",
                            "Interactive chart generated from your query results",
                        )

                        try:
                            if len(result.columns) >= 2:
                                chart_data = result.copy()
                                chart_data = chart_data.dropna(how="all")

                                if chart_data.empty:
                                    st.info("ℹ️ No data is available for visualization.", icon="ℹ️")
                                else:
                                    fig, rendered_type = build_plotly_figure(chart_data, chart_type, primary_yellow, primary_black)
                                    st.session_state.last_chart_fig = fig
                                    st.markdown(
                                        f"""
                                        <div class="chart-container">
                                            <div class="chart-meta">
                                                <span class="chart-meta-label">Chart type</span>
                                                <span class="chart-type-badge">{rendered_type}</span>
                                            </div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("ℹ️ At least 2 columns are required for visualization.", icon="ℹ️")

                        except ValueError as ve:
                            st.warning(f"⚠️ {str(ve)}", icon="⚠️")
                        except Exception as e:
                            st.error(f"📊 Visualization Error: {str(e)}", icon="❌")

                        # AI Insights
                        render_section_header(
                            "🧠",
                            "AI Insights",
                            "AI-powered analysis and recommendations based on your results",
                        )
                        st.markdown(
                            """
                            <div class="panel-header" style="margin-bottom:0.75rem;">
                                <div class="panel-header-text">
                                    <p class="panel-eyebrow">Analysis</p>
                                    <p class="panel-title">Business insights</p>
                                </div>
                                <span class="panel-badge">Step 3 of 3</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        insight_prompt = f"""
Analyze these query results and provide 3 concise, actionable business insights:

{result.to_string()}

Format your response as a numbered list with clear, practical insights."""

                        try:
                            with st.spinner("🤖 Generating insights..."):
                                insight_response = model.generate_content(insight_prompt)

                            st.session_state.last_insights = insight_response.text
                            st.markdown(
                                f"<div class='insights-panel'>{insight_response.text.replace(chr(10), '<br>')}</div>",
                                unsafe_allow_html=True
                            )
                        except Exception as e:

                            st.warning(
                                "⚠️ AI insights are currently unavailable. "
                                "Showing basic analytics instead.",
                                icon="⚠️"
                            )

                            # Generate basic analytics as fallback
                            basic_insights = f"📈 Quick Insights\n• Total Rows Returned: {len(result)}\n"
                            
                            numeric_cols = result.select_dtypes(
                                include=["number"]
                            ).columns

                            if len(numeric_cols) > 0:
                                main_col = numeric_cols[0]
                                basic_insights += f"• Highest {main_col}: {result[main_col].max():,.2f}\n"
                                basic_insights += f"• Average {main_col}: {result[main_col].mean():,.2f}\n"
                                basic_insights += f"• Lowest {main_col}: {result[main_col].min():,.2f}"
                            
                            st.session_state.last_insights = basic_insights

                            st.markdown(
                                "<div class='insights-panel'>",
                                unsafe_allow_html=True
                            )

                            st.markdown("### 📈 Quick Insights")

                            st.write(f"• Total Rows Returned: {len(result)}")

                            if len(numeric_cols) > 0:

                                main_col = numeric_cols[0]

                                st.write(
                                    f"• Highest {main_col}: "
                                    f"{result[main_col].max():,.2f}"
                                )

                                st.write(
                                    f"• Average {main_col}: "
                                    f"{result[main_col].mean():,.2f}"
                                )

                                st.write(
                                    f"• Lowest {main_col}: "
                                    f"{result[main_col].min():,.2f}"
                                )

                            st.markdown(
                                "</div>",
                                unsafe_allow_html=True
                            )

                except Exception as e:
                    st.error(f"❌ {format_api_error(e)}", icon="❌")

    st.markdown('<p class="action-bar-note">Results include SQL, data table, KPIs, charts, and AI insights</p>', unsafe_allow_html=True)

else:
    # Empty State
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-state-icon">📁</div>
            <h2 class="empty-state-title">Get Started</h2>
            <p class="empty-state-desc">
                Upload a CSV or Excel file to begin your data analysis journey.
                Ask questions in plain English and receive instant SQL, charts, and insights.
            </p>
            <div class="empty-state-tips">
                <div class="empty-state-tip">
                    <strong>Upload</strong>
                    Use the upload panel above to select your CSV or Excel file.
                </div>
                <div class="empty-state-tip">
                    <strong>Supported</strong>
                    CSV (.csv), Excel (.xlsx, .xls) with automatic sheet detection.
                </div>
                <div class="empty-state-tip">
                    <strong>Analyze</strong>
                    Ask natural language questions and get SQL, KPIs, and visualizations.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

render_footer()