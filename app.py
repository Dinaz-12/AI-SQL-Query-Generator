from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY").strip()

print("Loaded:", API_KEY[:10])

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

response = model.generate_content(
    "Convert to SQL: Show customers with salary above 100000"
)

print(response.text)