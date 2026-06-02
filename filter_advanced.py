import pandas as pd
import urllib.request

def create_advanced_corpus(input_csv, output_csv):
    print("Loading your Master CSAT Corpus...")
    df = pd.read_csv(input_csv)
    
    print("Downloading the Middle-School Baseline vocabulary list...")
    # We use a famous open-source linguistic repository of common English words
    url = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-no-swears.txt"
    response = urllib.request.urlopen(url)
    all_words = response.read().decode('utf-8').splitlines()
    
    # We take the top 2,500 conversational words to represent "Too Easy"
    # You can change this number! (e.g., 3000 for an even harder final list)
    basic_words = set(all_words[:2500])
    
    # We can also add a few CSAT Listening-specific junk words just in case
    custom_easy_words = {"mr", "mrs", "ms", "yeah", "oh", "hey", "hello", "hi", "okay", "bye"}
    basic_words.update(custom_easy_words)
    
    print(f"Subtracting {len(basic_words)} basic words from your database...")
    
    # THE MAGIC: Keep only the words that are NOT in the basic list!
    advanced_df = df[~df['Target Word'].isin(basic_words)].copy()
    
    # Save the new filtered database
    advanced_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    
    print(f"\n✅ Advanced Corpus created! Saved to {output_csv}")
    print(f"Original word count: {len(df)}")
    print(f"New Advanced word count: {len(advanced_df)}")
    print(f"Successfully deleted {len(df) - len(advanced_df)} easy/middle-school words.")

if __name__ == "__main__":
    # Make sure this matches the name of your current spreadsheet
    input_database = "CSAT_Weighted_Corpus.csv"
    output_database = "CSAT_Advanced_Target_70.csv"
    
    create_advanced_corpus(input_database, output_database)