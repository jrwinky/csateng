import pandas as pd
import urllib.request
import json

def create_pedagogical_corpus(input_csv, output_csv):
    print("Loading Master CSAT Corpus...")
    df = pd.read_csv(input_csv)
    
    print("Downloading Pedagogical ESL/Middle-School baselines...")
    try:
        url = "https://raw.githubusercontent.com/words/dale-chall/master/dale-chall.json"
        response = urllib.request.urlopen(url)
        dale_chall_words = set(json.loads(response.read().decode('utf-8')))
    except Exception as e:
        print("Could not download Dale-Chall. Make sure you have internet access.")
        dale_chall_words = set()

    # Custom CSAT easy words and listening test filler
    custom_easy_words = {
        "yeah", "oh", "hey", "hello", "hi", "okay", "bye", "yes", "no", 
        "mr", "mrs", "ms", "smile", "laugh", "cry", "percent", "percentage"
    }
    master_easy_filter = dale_chall_words.union(custom_easy_words)
    
    print(f"Subtracting {len(master_easy_filter)} pedagogical foundational words...")
    advanced_df = df[~df['Target Word'].isin(master_easy_filter)].copy()
    
    advanced_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"\n✅ Pedagogical Corpus created! Saved to {output_csv}")
    print(f"Successfully deleted {len(df) - len(advanced_df)} foundational words.")

if __name__ == "__main__":
    create_pedagogical_corpus("CSAT_Weighted_Corpus.csv", "CSAT_Advanced_Target_70.csv")