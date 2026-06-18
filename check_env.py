import os
import sys

print("Python version:", sys.version)

packages = [
    "google.generativeai",
    "streamlit",
    "pandas",
    "openpyxl",
    "streamlit_gsheets",
    "gspread"
]

print("\nChecking packages:")
for p in packages:
    try:
        __import__(p)
        print(f"  - {p}: Installed")
    except ImportError:
        print(f"  - {p}: NOT Installed")

print("\nChecking environment variables (presence only):")
env_keys = ["GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY", "PORT"]
for key in env_keys:
    val = os.environ.get(key)
    if val:
        print(f"  - {key}: Present (length {len(val)})")
    else:
        print(f"  - {key}: NOT Present")
