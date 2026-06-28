import spacy
import os
import glob
import pandas as pd
import re
from collections import Counter

BASIC_WORDS_FILTER = {"make", "find", "take", "time", "year", "people", "use", "good", "way", "day"}

def build_advanced_csat_corpus(input_folder, output_csv, current_year=2025, decay_rate=0.95, csat_multiplier=1.5):
    print("Loading spaCy English NLP model...")
    nlp = spacy.load("en_core_web_sm")
    word_frequencies = Counter()
    
    txt_files = glob.glob(os.path.join(input_folder, "*.txt"))
    if not txt_files:
        print(f"No text files found in {input_folder}!")
        return

    print(f"Found {len(txt_files)} exams. Applying Time Decay and Choice Multipliers...\n")
    
    for file_path in txt_files:
        filename = os.path.basename(file_path)
        
        # --- TIME DECAY CALCULATION ---
        try:
            exam_year = int(filename[:4])
            years_old = current_year - exam_year
            final_file_weight = decay_rate ** max(0, years_old)
        except ValueError:
            final_file_weight = 1.0 

        with open(file_path, "r", encoding="utf-8-sig") as f:
            raw_text = f.read()

        # --- ADVANCED OPTION HUNTER ---
        # Grabs chunks after ①②③④⑤ until a period, next option, new line, or EOF
        choice_pattern = re.compile(r'[①②③④⑤](.*?)(?=\.|[①②③④⑤]|\n\s*\d+\.|$)', re.DOTALL)
        raw_choice_chunks = choice_pattern.findall(raw_text)
        
        target_choice_lemmas = set()
        for chunk in raw_choice_chunks:
            chunk_doc = nlp(chunk)
            for token in chunk_doc:
                if token.is_alpha and not token.is_stop and token.pos_ in ["NOUN", "VERB", "ADJ", "ADV"]:
                    target_choice_lemmas.add(token.lemma_.lower())

        # --- FULL DOCUMENT PROCESSING ---
        nlp.max_length = len(raw_text) + 100000 
        doc = nlp(raw_text)
        
        for token in doc:
            if token.is_stop or token.is_punct or not token.is_alpha or not token.text.isascii():
                continue
            if token.pos_ not in ["NOUN", "VERB", "ADJ", "ADV"]:
                continue
                
            lemma = token.lemma_.lower()
            if len(lemma) <= 2 or lemma in BASIC_WORDS_FILTER:
                continue
                
            # Apply standard time weight
            weight_to_add = final_file_weight
            
            # Boost the weight if the word was found in a multiple choice option!
            if lemma in target_choice_lemmas:
                weight_to_add *= csat_multiplier
                
            word_frequencies[lemma] += weight_to_add

    print("\n✅ Advanced Extraction Complete! Formatting the data...")
    df = pd.DataFrame(word_frequencies.items(), columns=["Target Word", "Weighted Score"])
    df["Weighted Score"] = df["Weighted Score"].round(2)
    df = df.sort_values(by="Weighted Score", ascending=False).reset_index(drop=True)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"🎉 Corpus successfully saved to {output_csv}!")

if __name__ == "__main__":
    # POINT THIS TO THE SILVER LAYER!
    build_advanced_csat_corpus("./csat_text_english", "CSAT_Weighted_Corpus.csv")