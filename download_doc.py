import requests
import os

doc_id = "1oPwUdmpPN0gw6jyGi51SgN1k7V49QRDO"
download_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
output_path = r"c:\Users\AD\Desktop\AI_DUC\Buoi 7\doc_content.txt"

print(f"Downloading doc from {download_url}...")
try:
    response = requests.get(download_url)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print("Download successful!")
        print(f"Size: {os.path.getsize(output_path)} bytes")
    else:
        print(f"Failed to download. Status code: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
