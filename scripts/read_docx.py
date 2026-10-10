import zipfile
import re

def extract_text(docx_path):
    with zipfile.ZipFile(docx_path) as z:
        xml_content = z.read('word/document.xml').decode('utf-8')
    
    matches = re.findall(r'<w:t[^>]*>(.*?)</w:t>', xml_content)
    return ''.join(matches)

if __name__ == "__main__":
    text = extract_text("24BCE1188&1038_DBMSProject.docx")
    with open("docx_full_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Extracted successfully. Length:", len(text))
