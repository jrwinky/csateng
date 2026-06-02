import spacy
import os
import glob
import math
from collections import Counter

# We use the same basic word filter so we are only comparing high-value words
BASIC_WORDS_FILTER = {"make", "find", "take", "time", "year", "people", "use", "good", "way", "day"}

def extract_vocab_from_files(file_list, nlp):
    """Reads a list of text files and returns a frequency Counter of core words."""
    vocab_counter = Counter()
    
    for file_path in file_list:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            raw_text = f.read()
            
        nlp.max_length = len(raw_text) + 100000 
        doc = nlp(raw_text)
        
        for token in doc:
            if token.is_stop or token.is_punct or not token.is_alpha:
                continue
            if not token.text.isascii():
                continue
            if token.pos_ not in ["NOUN", "VERB", "ADJ", "ADV"]:
                continue
                
            lemma = token.lemma_.lower()
            if len(lemma) <= 2 or lemma in BASIC_WORDS_FILTER:
                continue
                
            vocab_counter[lemma] += 1
            
    return vocab_counter

def calculate_cosine_similarity(vec1, vec2):
    """Calculates the mathematical cosine similarity between two vocabulary vectors."""
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    
    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    
    if not denominator:
        return 0.0
    return float(numerator) / denominator

def calculate_top_n_overlap(vec1, vec2, top_n=300):
    """Calculates the percentage overlap of the top N most frequent words."""
    top1 = set([word for word, count in vec1.most_common(top_n)])
    top2 = set([word for word, count in vec2.most_common(top_n)])
    
    overlap = len(top1 & top2)
    return (overlap / top_n) * 100

def run_historical_comparison(input_folder):
    print("Loading spaCy NLP Model...")
    nlp = spacy.load("en_core_web_sm")
    
    # Define our historical buckets
    periods = {
        "Era 1 (2006-2012)": [],
        "Era 2 (2013-2016)": [],
        "Era 3 (2017-2025)": []
    }
    
    txt_files = glob.glob(os.path.join(input_folder, "*.txt"))
    
    # Sort the files by year
    for file_path in txt_files:
        filename = os.path.basename(file_path)
        try:
            year = int(filename[:4])
            if 2006 <= year <= 2012:
                periods["Era 1 (2006-2012)"].append(file_path)
            elif 2013 <= year <= 2016:
                periods["Era 2 (2013-2016)"].append(file_path)
            elif year >= 2017:
                periods["Era 3 (2017-2025)"].append(file_path)
        except ValueError:
            continue
            
    print(f"\nFiles sorted. Extracting vocabulary vectors...")
    vectors = {}
    for era_name, files in periods.items():
        print(f"Analyzing {era_name} ({len(files)} exams)...")
        vectors[era_name] = extract_vocab_from_files(files, nlp)

    # --- THE MATH & COMPARISON PHASE ---
    print("\n" + "="*50)
    print("📈 CORPUS SIMILARITY REPORT")
    print("="*50)
    
    # Compare Era 1 to the Modern Era (Era 3)
    cos_sim_1_3 = calculate_cosine_similarity(vectors["Era 1 (2006-2012)"], vectors["Era 3 (2017-2025)"])
    overlap_1_3 = calculate_top_n_overlap(vectors["Era 1 (2006-2012)"], vectors["Era 3 (2017-2025)"])
    
    # Compare Era 2 to the Modern Era (Era 3)
    cos_sim_2_3 = calculate_cosine_similarity(vectors["Era 2 (2013-2016)"], vectors["Era 3 (2017-2025)"])
    overlap_2_3 = calculate_top_n_overlap(vectors["Era 2 (2013-2016)"], vectors["Era 3 (2017-2025)"])
    
    print(f"Comparing: Era 1 (Pre-2013) vs. Era 3 (Modern)")
    print(f" - Cosine Similarity: {cos_sim_1_3:.3f}")
    print(f" - Top 300 Overlap:   {overlap_1_3:.1f}%\n")
    
    print(f"Comparing: Era 2 (2013-2016) vs. Era 3 (Modern)")
    print(f" - Cosine Similarity: {cos_sim_2_3:.3f}")
    print(f" - Top 300 Overlap:   {overlap_2_3:.1f}%\n")
    
    print("="*50)
    print("🧠 DATA DECISION GUIDE:")
    print("If Cosine > 0.85: The older exams are highly relevant. KEEP THEM to enrich the model.")
    print("If Cosine < 0.70: The vocabulary has shifted significantly. EXCLUDE THEM or heavily decay them.")
    print("="*50)

if __name__ == "__main__":
    # Point this to your folder of 53 text files!
    input_directory = "C:/Users/aaron/Documents/Aaron/Seoulrun/pastexamtexts" 
    run_historical_comparison(input_directory)