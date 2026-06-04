import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import sqlite3
import pandas as pd
import plotly.express as px

# -----------------------------
# Page Config (MUST BE FIRST)
# -----------------------------
st.set_page_config(
    page_title="AI Data Analyst Assistant",
    page_icon="di_logo.png",
    layout="wide"
)

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY").strip()
)

model = genai.GenerativeModel("gemini-2.5-flash")

# -----------------------------
# Session State
# -----------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:

    st.image(
        "di_logo.png",
        width=180
    )

    st.header("📝 Query History")

    for item in st.session_state.history:
        st.write("•", item)

# -----------------------------
# Main UI
# -----------------------------

st.title("AI Data Analyst Assistant")

st.caption(
    "Upload a CSV file and ask questions in plain English."
)
# -----------------------------
# Upload CSV
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload CSV File",
    type=["csv"]
)

if uploaded_file is not None:

    # Read CSV
    df = pd.read_csv(uploaded_file)

    # Dataset Summary
    with st.sidebar:

        st.divider()
        st.header("📊 Dataset Summary")

        st.write(f"Rows: {df.shape[0]}")
        st.write(f"Columns: {df.shape[1]}")

    # Save to SQLite
    conn = sqlite3.connect("database.db")

    df.to_sql(
        "uploaded_data",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    st.success("✅ Dataset uploaded successfully!")

    # Preview
    st.subheader("Dataset Preview")

    st.dataframe(
        df.head(),
        hide_index=True
    )

    # Metrics
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Rows", df.shape[0])

    with col2:
        st.metric("Columns", df.shape[1])

    # Show Columns
    st.subheader("Columns")
    st.write(list(df.columns))

    # Question Input
    user_input = st.text_area(
        "Ask a question about your data",
        placeholder="Example: Show top 5 customers by sales"
    )

    # Generate Button
    if st.button("Generate Insights"):

        if user_input.strip() == "":
            st.warning("Please enter a question.")
            st.stop()

        st.session_state.history.append(user_input)

        columns = ", ".join(df.columns)

        prompt = f"""
You are an SQL expert.

Database Table:
uploaded_data

Columns:
{columns}

Rules:
1. Return ONLY SQL.
2. No explanation.
3. No markdown.
4. Use only uploaded_data table.
5. Always use aliases for aggregate columns.

Examples:
COUNT(*) AS TotalCount
SUM(Sales) AS TotalSales
AVG(Salary) AS AverageSalary

User Request:
{user_input}
"""

        try:

            # Generate SQL
            with st.spinner("Generating SQL..."):

                response = model.generate_content(
                    prompt
                )

            sql_query = response.text.strip()

            if sql_query.upper().count("SELECT") > 1:

                st.error(
                    "Please ask only one question at a time."
                )

                st.stop()

            # Safety Check
            if not sql_query.upper().startswith("SELECT"):

                st.error(
                    "Only SELECT queries are allowed."
                )

                st.stop()

            # Show SQL
            st.subheader("Generated SQL")

            st.code(
                sql_query,
                language="sql"
            )

            # Execute Query
            conn = sqlite3.connect(
                "database.db"
            )

            result = pd.read_sql_query(
                sql_query,
                conn
            )

            conn.close()

            # Show Results
            st.subheader("Results")

            st.dataframe(
                result,
                hide_index=True
            )



            # -----------------
            # Auto Chart
            # -----------------
            # -----------------
            # Visualization
            # -----------------
            st.subheader("📊 Visualization")

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
                            title=f"{chart_data.columns[1]} by {chart_data.columns[0]}"
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True
                        )

                    else:

                        st.info(
                            "No numeric data available for visualization."
                        )

                else:

                    st.info(
                        "At least 2 columns are required for visualization."
                    )

            except Exception as e:

                st.error(
                    f"Chart Error: {e}"
                )

            # -----------------
            # AI Insights
            # -----------------
            insight_prompt = f"""
Analyze the following query results:

{result.to_string()}

Give 3 short business insights.
"""

            with st.spinner(
                "Generating AI insights..."
            ):

                insight_response = (
                    model.generate_content(
                        insight_prompt
                    )
                )

            st.subheader("🧠 AI Insights")

            st.write(
                insight_response.text
            )

            # -----------------
            # Download CSV
            # -----------------
            csv = result.to_csv(
                index=False
            )

            st.download_button(
                label="📥 Download Results",
                data=csv,
                file_name="results.csv",
                mime="text/csv"
            )

        except Exception as e:

            st.error(
                f"Error: {e}"
            )

else:

    st.info(
        "Upload a CSV file to begin."
    )