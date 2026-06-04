import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import sqlite3
import pandas as pd

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(
    api_key=os.getenv("GEMINI_API_KEY").strip()
)

model = genai.GenerativeModel("gemini-2.5-flash")

# UI
st.title("🤖 AI SQL Query Generator")
st.caption("Convert natural language into SQL queries and execute them instantly.")

user_input = st.text_area(
    "Enter your question",
    placeholder="Example: Show customers with salary above 100000"
)

if st.button("Generate SQL"):

    prompt = f"""
    You are an SQL expert.

    Database Schema:

    Table: customers

    Columns:
    id
    name
    salary
    city

    Rules:
    1. Return only SQL.
    2. No explanation.
    3. No markdown.
    4. Use only the customers table.

    Request:
    {user_input}
    """

    try:

        # Generate SQL
        with st.spinner("Generating SQL..."):
            response = model.generate_content(prompt)

        sql_query = response.text.strip()

        # Display SQL
        st.subheader("Generated SQL")
        st.code(sql_query, language="sql")

        # Execute SQL
        conn = sqlite3.connect("database.db")

        result = pd.read_sql_query(
            sql_query,
            conn
        )

        conn.close()

        # Display Results
        st.subheader("Results")
        st.dataframe(
            result,
            hide_index=True
        )

        # Download Button
        csv = result.to_csv(index=False)

        st.download_button(
            label="📥 Download Results",
            data=csv,
            file_name="results.csv",
            mime="text/csv"
        )

    except Exception as e:

        st.error(f"Error: {e}")