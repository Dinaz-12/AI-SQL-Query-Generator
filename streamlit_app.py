import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
        "Upload your CSV and ask questions in plain English.</p>",
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
    "Choose a CSV file",
    type=["csv"],
    help="Select a CSV file to analyze with AI"
)

if uploaded_file is not None:

    # Read CSV
    df = pd.read_csv(uploaded_file)

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
            f"<div class='metric-card'><div class='metric-label'>Data Size</div><div class='metric-value'>{uploaded_file.size / 1024:.1f} KB</div></div>",
            unsafe_allow_html=True
        )

    # Save to SQLite
    conn = sqlite3.connect("database.db")

    df.to_sql(
        "uploaded_data",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

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

                        # Visualization
                        st.markdown(
                            f"<h2 class='section-header'>📊 Visualization</h2>",
                            unsafe_allow_html=True
                        )

                        try:
                            if len(result.columns) >= 2:
                                chart_data = result.copy()

                                # Convert second column to numeric
                                chart_data.iloc[:, 1] = pd.to_numeric(
                                    chart_data.iloc[:, 1],
                                    errors="coerce"
                                )

                                chart_data = chart_data.dropna()

                                if not chart_data.empty:
                                    fig = px.bar(
                                        chart_data,
                                        x=chart_data.columns[0],
                                        y=chart_data.columns[1],
                                        title=f"{chart_data.columns[1]} by {chart_data.columns[0]}",
                                        labels={
                                            chart_data.columns[0]: chart_data.columns[0],
                                            chart_data.columns[1]: chart_data.columns[1]
                                        },
                                        color_discrete_sequence=[primary_yellow]
                                    )
                                    
                                    fig.update_layout(
                                        plot_bgcolor="white",
                                        paper_bgcolor="white",
                                        font=dict(family="Arial", size=12, color=primary_black),
                                        title_font_size=16,
                                        height=450,
                                        showlegend=False,
                                        hovermode="x unified"
                                    )
                                    
                                    fig.update_xaxes(
                                        showgrid=True,
                                        gridwidth=1,
                                        gridcolor="#f0f0f0"
                                    )
                                    
                                    fig.update_yaxes(
                                        showgrid=True,
                                        gridwidth=1,
                                        gridcolor="#f0f0f0"
                                    )

                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info("ℹ️ No numeric data available for visualization.", icon="ℹ️")
                            else:
                                st.info("ℹ️ At least 2 columns are required for visualization.", icon="ℹ️")

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

                            st.markdown(
                                "<div class='card'>",
                                unsafe_allow_html=True
                            )

                            st.markdown("### 📈 Quick Insights")

                            st.write(f"• Total Rows Returned: {len(result)}")

                            numeric_cols = result.select_dtypes(
                                include=["number"]
                            ).columns

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
            f"Upload a CSV file to begin your data analysis journey with AI-powered SQL generation.</p>"
            f"<div style='background: linear-gradient(135deg, {primary_yellow}15 0%, transparent 100%); "
            f"border: 2px dashed {primary_yellow}; border-radius: 12px; padding: 2rem; "
            f"color: #666; font-size: 0.95rem;'>"
            f"👆 Use the upload area above to select your CSV file<br><br>"
            f"✨ Supported formats: CSV files with any number of columns<br><br>"
            f"🚀 Ask questions in plain English and get instant SQL queries"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )