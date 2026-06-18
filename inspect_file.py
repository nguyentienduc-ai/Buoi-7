path = r"c:\Users\AD\Desktop\AI_DUC\Buoi 7\data_raw.xlsx"

try:
    with open(path, "rb") as f:
        bytes_content = f.read(100)
        print("First 100 bytes (hex):", bytes_content.hex())
        print("First 100 bytes (text):", bytes_content)
except Exception as e:
    print(f"Error: {e}")

