import zipfile
import re
import os

pptx_path = r"c:\Users\AD\Desktop\AI_DUC\Buoi 7\MindX_AG_Slide 7.pptx"

if not os.path.exists(pptx_path):
    print("PPTX file not found!")
    exit(1)

try:
    with zipfile.ZipFile(pptx_path, 'r') as z:
        print("Searching all .rels files in zip:")
        for name in z.namelist():
            if name.endswith('.rels'):
                content = z.read(name).decode('utf-8', errors='ignore')
                urls = re.findall(r'Target="([^"]+)"', content)
                # Only print if there's any HTTP/HTTPS link or drive links
                web_urls = [u for u in urls if u.startswith('http')]
                if web_urls:
                    print(f"\nFile: {name}")
                    for u in web_urls:
                        print(f"  - {u}")
except Exception as e:
    print(f"Error: {e}")

