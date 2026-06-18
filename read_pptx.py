import zipfile
import re
import os

pptx_path = r"c:\Users\AD\Desktop\AI_DUC\Buoi 7\MindX_AG_Slide 7.pptx"
output_path = r"c:\Users\AD\Desktop\AI_DUC\Buoi 7\slide_content.txt"

if not os.path.exists(pptx_path):
    print("PPTX file not found!")
    exit(1)

try:
    with zipfile.ZipFile(pptx_path, 'r') as z:
        slides_content = []
        # Find all slide xml files
        slide_files = [f for f in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml', f)]
        # Sort them by slide number
        slide_files.sort(key=lambda x: int(re.search(r'\d+', x).group()))
        
        for f in slide_files:
            xml_content = z.read(f).decode('utf-8')
            # Find all text elements. In PPTX XML, text is usually inside <a:t>...</a:t>
            texts = re.findall(r'<a:t>(.*?)</a:t>', xml_content)
            slide_num = re.search(r'\d+', f).group()
            slides_content.append(f"--- SLIDE {slide_num} ---")
            slides_content.append("\n".join(texts))
            slides_content.append("\n")

    with open(output_path, 'w', encoding='utf-8') as out:
        out.write("\n".join(slides_content))

    print(f"Successfully extracted text to {output_path}")
except Exception as e:
    print(f"Error extracting slide content: {e}")
