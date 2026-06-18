import requests
import pandas as pd
import os

sheet_id = "16tCAf_qqtgYZxoumYQKMEOdBhKE0wg5A"
download_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

output_path = r"c:\Users\AD\Desktop\AI_DUC\Buoi 7\data_leads.xlsx"

print(f"Downloading leads from {download_url}...")
try:
    response = requests.get(download_url)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print("Download successful!")
        
        # Verify and read
        df = pd.read_excel(output_path)
        print("Columns in file:", df.columns.tolist())
        print("Shape:", df.shape)
        print("First 5 rows:")
        print(df.head())
    else:
        print(f"Failed to download. Status code: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
