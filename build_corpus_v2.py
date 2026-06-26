import spacy
import os
import glob
import pandas as pd
from collections import Counter
from dotenv import load_dotenv
import re

# Add any basic middle-school words here that you want to instantly delete
# so your 70-point target student only gets high-level vocabulary.
BASIC_WORDS_FILTER = {"make", "find", "take", "time", "year", "people", "use", "good", "way", "day"}

def build_advanced_csat_corpus(input_folder, output_csv, current_year=2025, decay_rate=0.95, csat_multiplier=1.2):
    print("Loading spaCy English NLP model...")
    nlp = spacy.load("en_core_web_sm")
    word_frequencies = Counter()
    
    txt_files = glob.glob(os.path.join(input_folder, "*.txt"))
    if not txt_files:
        print(f"No text files found in {input_folder}!")
        return

    print(f"Found {len(txt_files)} exams. Applying Time Decay and CSAT Multipliers...\n")
    
    for i, file_path in enumerate(txt_files):
        filename = os.path.basename(file_path)
        
        # --- WEIGHT CALCULATION ---
        # Extract the year and month from the filename (e.g., 20241114.txt)
        try:
            exam_year = int(filename[:4])
            exam_month = int(filename[4:6])
        except ValueError:
            print(f"Skipping {filename}: Invalid date format.")
            continue
            
        # 1. Time Decay: Older exams get exponentially less weight
        years_old = current_year - exam_year
        time_weight = decay_rate ** years_old
        
        # 2. Source Authority: November exams (대수능) get a boost
        authority_weight = csat_multiplier if exam_month == (11 or 12) else 1.0
        
        # Calculate Final Multiplier for this specific exam
        final_file_weight = time_weight * authority_weight
        
        print(f"[{i+1}/{len(txt_files)}] {filename} | Year: {exam_year} | Multiplier: {final_file_weight:.2f}x")
        
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
            
        # --- THE QUESTION 1-5 TRICK ---
        # To apply weights to questions 1-5 (Listening), we can use Regex to boost words 
        # that appear early in the document. For now, we apply the file weight globally.
            
        nlp.max_length = len(raw_text) + 100000 
        doc = nlp(raw_text)
        
        for token in doc:
            # We keep the alpha filter to remove stray numbers/punctuation
            if token.is_stop or token.is_punct or not token.is_alpha:
                continue
                
            if token.pos_ not in ["NOUN", "VERB", "ADJ", "ADV"]:
                continue
                
            lemma = token.lemma_.lower()
            
            # Skip tiny words and our basic word filter
            if len(lemma) <= 2 or lemma in BASIC_WORDS_FILTER:
                continue
                
            # THE MAGIC: Instead of +1, we add the mathematical weight!
            word_frequencies[lemma] += final_file_weight

    print("\n✅ Advanced Extraction Complete! Formatting the data...")
    
    # Round the weights to 2 decimal places for clean viewing in Excel
    df = pd.DataFrame(word_frequencies.items(), columns=["Target Word", "Weighted Score"])
    df["Weighted Score"] = df["Weighted Score"].round(2)
    df = df.sort_values(by="Weighted Score", ascending=False).reset_index(drop=True)
    
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"🎉 Corpus successfully saved to {output_csv}!")

if __name__ == "__main__":
    load_dotenv()

    input_directory = os.getenv("ENG_PATH")
    output_database = "CSAT_Weighted_Corpus.csv"
    
    # You can easily tweak your parameters here!
    build_advanced_csat_corpus(input_directory, output_database, decay_rate=0.95, csat_multiplier=1.2)