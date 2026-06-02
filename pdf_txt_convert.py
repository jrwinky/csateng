import concurrent.futures
import os
import glob
import pdfplumber
import re

def extract_and_sanitize_csat_pdf(pdf_path, raw_txt_path, english_txt_path):
    full_exam_text = ""
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            width = page.width
            height = page.height
            
            left_bbox = (0, 0, width * 0.5, height)
            right_bbox = (width * 0.5, 0, width, height)
            
            extraction_params = {
                "x_tolerance": 2,
                "y_tolerance": 3,
                "keep_blank_chars": True
            }
            
            left_text = page.within_bbox(left_bbox).extract_text(**extraction_params)
            right_text = page.within_bbox(right_bbox).extract_text(**extraction_params)
            
            if left_text: full_exam_text += left_text + "\n\n"
            if right_text: full_exam_text += right_text + "\n\n"

    if not full_exam_text.strip():
        raise ValueError("No text extracted. Likely a scanned image PDF.")

    # ==========================================
    # 1. SAVE THE BRONZE LAYER (Untouched Archive)
    # ==========================================
    with open(raw_txt_path, "w", encoding="utf-8-sig") as f:
        f.write(full_exam_text)

    # ==========================================
    # 2. SMART CLEANING FOR THE SILVER LAYER
    # ==========================================
    
    # STEP A: Remove full Korean instruction lines (e.g., "18. 다음 글의 목적으로 가장 적절한 것은?")
    # This prevents leaving "ghost" question numbers floating in the text.
    # It looks for a number, a period, and Korean characters, and deletes the whole line.
    clean_text = re.sub(r'\d+\.\s*[가-힣].*?\n', '\n', full_exam_text)
    
    # STEP B: Remove any leftover Korean characters (translations, footnotes)
    clean_text = re.sub(r'[가-힣ㄱ-ㅎㅏ-ㅣ]', '', clean_text)
    
    # STEP C: Clean up empty multiple-choice options (e.g., if a Korean option became "① ")
    # This deletes circled numbers that have no English words next to them.
    clean_text = re.sub(r'[①②③④⑤]\s*\n', '\n', clean_text)

    # ==========================================
    # 3. SAVE THE SILVER LAYER (English-Only NLP Ready)
    # ==========================================
    with open(english_txt_path, "w", encoding="utf-8-sig") as f:
        f.write(clean_text)

def process_single_file(pdf_path, raw_folder, english_folder):
    """Routes the files to their proper directories."""
    base_name = os.path.basename(pdf_path)
    txt_name = base_name.replace(".pdf", ".txt")
    
    raw_txt_path = os.path.join(raw_folder, txt_name)
    english_txt_path = os.path.join(english_folder, txt_name)
    
    try:
        extract_and_sanitize_csat_pdf(pdf_path, raw_txt_path, english_txt_path)
        return f"✅ Success: {txt_name} (Saved to Raw & English folders)"
    except Exception as e:
        return f"❌ FAILED on {txt_name} - Reason: {e}"

def batch_process_directory_fast(input_folder, raw_folder, english_folder):
    # Create BOTH directories
    os.makedirs(raw_folder, exist_ok=True)
    os.makedirs(english_folder, exist_ok=True)
    
    search_pattern = os.path.join(input_folder, "*.pdf")
    pdf_files = glob.glob(search_pattern)
    
    if not pdf_files:
        print(f"No PDFs found in {input_folder}")
        return

    print(f"Found {len(pdf_files)} PDFs. Extracting to Dual-Directories...\n")
    
    executor = concurrent.futures.ProcessPoolExecutor()
    futures = [executor.submit(process_single_file, pdf, raw_folder, english_folder) for pdf in pdf_files]
    
    for future in concurrent.futures.as_completed(futures):
        print(future.result())
            
    print("\n🚀 Master Conversion Complete!")
    os._exit(0)

if __name__ == "__main__":
    pdf_dir = "C:/Users/aaron/Documents/Aaron/Seoulrun/pastexams"
    
    # The Dual-Export Folders!
    raw_txt_dir = "C:/Users/aaron/Documents/Aaron/Seoulrun/pastexamsrawtexts"
    english_txt_dir = "C:/Users/aaron/Documents/Aaron/Seoulrun/pastexamsengtexts"
    
    batch_process_directory_fast(pdf_dir, raw_txt_dir, english_txt_dir)