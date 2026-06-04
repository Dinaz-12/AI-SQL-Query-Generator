import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import sqlite3
import pandas as pd

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY").strip()
)

model = genai.GenerativeModel("gemini-2.5-flash")

st.title("AI SQL Query Generator")

user_input = st.text_area(
    "Enter your question"
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
    1. Return only SQL
    2. No explanation
    3. No markdown
    4. Use only the customers table

    Request:
    {user_input}
    """

    response = model.generate_content(prompt)

    sql_query = response.text.strip()

    st.subheader("Generated SQL")
    st.code(sql_query, language="sql")

    try:

        conn = sqlite3.connect("database.db")

        result = pd.read_sql_query(
            sql_query,
            conn
        )

        st.subheader("Results")
        st.dataframe(result)

        conn.close()

    except Exception as e:

        st.error(f"Error: {e}")