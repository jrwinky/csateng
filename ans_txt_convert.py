import easyocr
import pdfplumber
import os
from PIL import Image

# Initialize the reader once (loading the model takes a moment)
# 'ko' for Korean, 'en' for English
reader = easyocr.Reader(['ko', 'en'])

def extract_text_from_file(file_path):
    """
    Extracts text from images or PDFs using EasyOCR.
    Handles multiple file formats efficiently without external dependencies.
    """
    ext = os.path.splitext(file_path)[1].lower()
    text_content = ""

    try:
        if ext in ['.jpg', '.png', '.jpeg']:
            # Perform OCR on image files directly
            results = reader.readtext(file_path, detail=0)
            text_content = "\n".join(results)
            
        elif ext == '.pdf':
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        
    return text_content

# --- Example Usage ---
# file_path = "20180607_A.jpg"
# extracted_text = extract_text_from_file(file_path)
# print(extracted_text)