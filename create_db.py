import sqlite3
import pandas as pd

df = pd.read_csv("data/customers.csv")

conn = sqlite3.connect("database.db")

df.to_sql(
    "customers",
    conn,
    if_exists="replace",
    index=False
)

conn.close()

print("Database Created Successfully!")