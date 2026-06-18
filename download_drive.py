import requests
import re
import os

url = "https://drive.google.com/file/d/1_2_EV4s9EPe0Ey5R7wNUR6Kwt8FiofJ6/view"
file_id = "1_2_EV4s9EPe0Ey5R7wNUR6Kwt8FiofJ6"
download_url = f"https://docs.google.com/uc?export=download&id={file_id}"

output_path = r"c:\Users\AD\Desktop\AI_DUC\Buoi 7\data_raw.xlsx"

print(f"Downloading from {download_url}...")
try:
    session = requests.Session()
    # First request to get the download page / confirmation if large
    response = session.get(download_url, stream=True)
    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break
            
    if token:
        confirm_url = download_url + f"&confirm={token}"
        response = session.get(confirm_url, stream=True)
        
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)
                
    print(f"Successfully downloaded to {output_path}")
    print(f"File size: {os.path.getsize(output_path)} bytes")
except Exception as e:
    print(f"Error: {e}")
