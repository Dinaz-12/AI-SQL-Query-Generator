import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
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
# Page Config (MUST BE FIRST)
# =============================================================================
st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="📊",
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

custom_css = f"""
<style>
    /* Primary Colors */
    :root {{
        --primary-yellow: {primary_yellow};
        --primary-black: {primary_black};
        --primary-white: {primary_white};
        --light-gray: {light_gray};
    }}

    /* Main Background */
    .stApp {{
        background-color: {primary_white};
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

    /* Containers & Cards */
    .card {{
        background-color: {light_gray};
        border-left: 4px solid {primary_yellow};
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }}

    /* Metric Boxes */
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

    /* KPI Cards */
    div[data-testid="stMetric"] {{
        border-radius: 18px !important;
        background-color: {primary_white} !important;
        border: 1px solid rgba(255, 193, 7, 0.18) !important;
        box-shadow: 0 20px 32px rgba(18, 18, 18, 0.06) !important;
        padding: 1.15rem 1.25rem !important;
        margin-bottom: 1rem !important;
        min-height: 124px;
    }}

    div[data-testid="stMetric"] > div > div:first-child {{
        color: #666 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.02em !important;
        margin-bottom: 0.4rem !important;
    }}

    div[data-testid="stMetric"] > div > div:nth-child(2) {{
        color: {primary_black} !important;
        font-size: 1.95rem !important;
        font-weight: 700 !important;
    }}

    /* Section Headers */
    .section-header {{
        color: {primary_black};
        font-size: 1.5rem;
        font-weight: 700;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid {primary_yellow};
        margin: 2rem 0 1rem 0;
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
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# =============================================================================
# Load Environment Variables
# =============================================================================
load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY").strip()
)

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
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial", size=12, color=primary_black),
        title_font_size=16,
        height=450,
        showlegend=False,
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#f0f0f0")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#f0f0f0")

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
    
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("📊 AI Data Analyst", title_style))
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

    st.markdown(
        f"<div class='section-header' style='margin-top: 1rem;'>📈 KPI Dashboard</div>",
        unsafe_allow_html=True
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
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"<h2 style='color: {primary_yellow}; font-size: 1.8rem; font-weight: 800; margin: 0;'>AI Data Analyst</h2>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(f"<div style='font-size: 2rem;'>📊</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 0.5px; background: rgba(255,193,7,0.3); margin: 1rem 0;'></div>", unsafe_allow_html=True)
    
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
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(
        f"<div style='text-align: center; padding: 2rem 0;'>"
        f"<h1 style='color: {primary_black}; font-size: 3rem; font-weight: 800; margin: 0;'>"
        f"✨ AI Data Analyst</h1>"
        f"<p style='color: #666; font-size: 1.1rem; margin-top: 0.5rem;'>"
        f"Generate SQL queries and insights from plain English</p>"
        f"</div>",
        unsafe_allow_html=True
    )

st.markdown(f"<div class='divider'></div>", unsafe_allow_html=True)

# =============================================================================
# Upload CSV Section
# =============================================================================
st.markdown(
    f"<h2 class='section-header'>📤 Upload Your Data</h2>",
    unsafe_allow_html=True
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
            f"<div class='metric-card'><div class='metric-label'>Total Rows</div><div class='metric-value'>{df.shape[0]:,}</div></div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='metric-card'><div class='metric-label'>Columns</div><div class='metric-value'>{df.shape[1]}</div></div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='metric-card'><div class='metric-label'>Data Size</div><div class='metric-value'>{file_size_kb:.1f} KB</div></div>",
            unsafe_allow_html=True
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
    st.markdown(
        f"<h2 class='section-header'>👁️ Data Preview</h2>",
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.dataframe(
            df.head(10),
            hide_index=True,
            use_container_width=True
        )
    with col2:
        st.markdown(
            f"<div class='card'><strong>Column Names</strong><br>"
            f"{'<br>'.join([f'🔹 {col}' for col in df.columns])}"
            f"</div>",
            unsafe_allow_html=True
        )

    # Question Input Section
    st.markdown(
        f"<h2 class='section-header'>❓ Ask a Question</h2>",
        unsafe_allow_html=True
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

    # Generate Button with formatting
    col1, col2, col3 = st.columns([1, 2, 1])
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
                    st.markdown(
                        f"<h2 class='section-header'>💾 Generated SQL</h2>",
                        unsafe_allow_html=True
                    )

                    st.code(sql_query, language="sql")

                    # Execute Query
                    conn = sqlite3.connect("database.db")

                    result = pd.read_sql_query(sql_query, conn)

                    conn.close()

                    # Display Results
                    st.markdown(
                        f"<h2 class='section-header'>📋 Results</h2>",
                        unsafe_allow_html=True
                    )

                    if result.empty:
                        st.info("ℹ️ The query returned no results. Try modifying your question.", icon="ℹ️")
                    else:
                        st.dataframe(
                            result,
                            hide_index=True,
                            use_container_width=True
                        )

                        generate_kpis(result)

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(
                                f"<div class='metric-card'><div class='metric-label'>Rows</div><div class='metric-value'>{len(result)}</div></div>",
                                unsafe_allow_html=True
                            )
                        with col2:
                            st.markdown(
                                f"<div class='metric-card'><div class='metric-label'>Columns</div><div class='metric-value'>{len(result.columns)}</div></div>",
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
                        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
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
                        st.markdown(
                            f"<h2 class='section-header'>📊 Visualization</h2>",
                            unsafe_allow_html=True
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
                                        f"<p style='color: #444; font-size: 0.95rem; margin-bottom: 1rem;'>" \
                                        f"Showing <strong>{rendered_type}</strong> for your query result.</p>",
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
                        st.markdown(
                            f"<h2 class='section-header'>🧠 AI Insights</h2>",
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
                                f"<div class='card'>{insight_response.text.replace(chr(10), '<br>')}</div>",
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
                                "<div class='card'>",
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

else:
    # Empty State
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            f"<div style='text-align: center; padding: 4rem 2rem;'>"
            f"<div style='font-size: 4rem; margin-bottom: 1rem;'>📁</div>"
            f"<h2 style='color: {primary_black}; font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem;'>"
            f"Get Started</h2>"
            f"<p style='color: #666; font-size: 1rem; line-height: 1.6; margin-bottom: 2rem;'>"
            f"Upload a CSV or Excel file to begin your data analysis journey with AI-powered SQL generation.</p>"
            f"<div style='background: linear-gradient(135deg, {primary_yellow}15 0%, transparent 100%); "
            f"border: 2px dashed {primary_yellow}; border-radius: 12px; padding: 2rem; "
            f"color: #666; font-size: 0.95rem;'>"
            f"👆 Use the upload area above to select your CSV or Excel file<br><br>"
            f"✨ Supported formats: CSV (.csv), Excel (.xlsx, .xls)<br><br>"
            f"🚀 Ask questions in plain English and get instant SQL queries"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )