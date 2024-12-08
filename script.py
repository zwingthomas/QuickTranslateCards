import json
import os
import random
import sys
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from googleapiclient.discovery import build

JSON_FILENAME = "words.json"
WORDS_FILENAME = "words.txt"
DOCUMENT_ID = "1GhFCgqgs7tTqrgVyvgIwMGVCuWjqCsr66YNb-cuUMwU"
SERVICE_ACCOUNT_FILE = "/Users/thomaszwinger/Documents/Dropcycle/jenkins/ansible/auth_gcp.json"
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

def load_words():
    # If JSON file doesn't exist, create it with empty "words"
    if not os.path.isfile(JSON_FILENAME):
        data = {"words": []}
        with open(JSON_FILENAME, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return data["words"]

    # If file exists, try loading it
    try:
        with open(JSON_FILENAME, "r", encoding="utf-8") as f:
            data = json.load(f)
            words = data.get("words", [])

            # Migrate existing data: ensure each word has weight_en_to_pt and weight_pt_to_en
            for w in words:
                # If the old "weight" field is present, use it and remove it.
                if "weight" in w:
                    old_weight = w["weight"]
                    w["weight_en_to_pt"] = old_weight
                    w["weight_pt_to_en"] = old_weight
                    del w["weight"]
                else:
                    # If no weight fields are present at all, set defaults
                    if "weight_en_to_pt" not in w:
                        w["weight_en_to_pt"] = 9
                    if "weight_pt_to_en" not in w:
                        w["weight_pt_to_en"] = 9

            # Save back the migrated version to keep consistency
            save_words(words)
            return words
    except (json.JSONDecodeError, FileNotFoundError):
        # If file is invalid JSON or can't be opened, create a new one
        data = {"words": []}
        with open(JSON_FILENAME, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return data["words"]

def save_words(words):
    data = {"words": words}
    # Make sure that no old 'weight' field is included
    # Just ensure we keep weight_en_to_pt and weight_pt_to_en
    for w in words:
        if "weight" in w:
            del w["weight"]

    with open(JSON_FILENAME, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def find_word(words_list, portuguese_word):
    for w in words_list:
        if w["portuguese"].lower() == portuguese_word.lower():
            return w
    return None

def add_new_word(words_list, portuguese_word, english_word):
    words_list.append({
        "portuguese": portuguese_word,
        "english": english_word,
        # Default weights
        "weight_en_to_pt": 9,
        "weight_pt_to_en": 9
    })
    save_words(words_list)
    
def translate_word(word, translate_client):
    # Translate from Portuguese (pt) to English (en)
    result = translate_client.translate(word, source_language='pt', target_language='en')
    return result['translatedText']

def weighted_random_choice(words_list, english_first):
    # Choose the appropriate weight based on the current mode
    # If english_first == True, we quiz English→Portuguese, so use weight_en_to_pt
    # Else, use weight_pt_to_en
    if english_first:
        weights = [w.get("weight_en_to_pt", 9) for w in words_list]
    else:
        weights = [w.get("weight_pt_to_en", 9) for w in words_list]

    total_weight = sum(w for w in weights if w > 0)
    if total_weight == 0:
        # If all weights are 0, just pick a random word
        return random.choice(words_list)

    r = random.uniform(0, total_weight)
    current = 0
    for idx, w_obj in enumerate(words_list):
        w = weights[idx]
        current += w
        if current >= r:
            return w_obj
    return random.choice(words_list)

def read_initial_words_from_file(filename):
    if not os.path.isfile(filename):
        print(f"Error: The words file '{filename}' does not exist.")
        return []
    words = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            w = line.strip()
            if w:
                words.append(w)
    return words

def append_new_word_to_file(word):
    # Check if the word already exists in words.txt (not strictly required, but good practice)
    if os.path.isfile(WORDS_FILENAME):
        with open(WORDS_FILENAME, "r", encoding="utf-8") as f:
            existing = {line.strip().lower() for line in f if line.strip()}
        if word.lower() in existing:
            return
    # Append the word
    with open(WORDS_FILENAME, "a", encoding="utf-8") as f:
        f.write(word + "\n")

def get_docs_service():
    # Create credentials from the service account JSON file
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('docs', 'v1', credentials=creds)
    return service

def fetch_phrases_from_doc(document_id):
    service = get_docs_service()
    doc = service.documents().get(documentId=document_id).execute()
    content = doc.get('body', {}).get('content', [])
    phrases = []
    for element in content:
        if 'paragraph' in element:
            paragraph = element['paragraph']
            for elem in paragraph.get('elements', []):
                text_run = elem.get('textRun')
                if text_run and 'content' in text_run:
                    text = text_run['content'].strip()
                    if text:
                        phrases.append(text)
    return phrases

def update_from_doc(words_list, translate_client):
    new_phrases = fetch_phrases_from_doc(DOCUMENT_ID)
    existing_portuguese = {w["portuguese"].lower() for w in words_list}
    to_add = [p for p in new_phrases if p.lower() not in existing_portuguese]

    if not to_add:
        print("No new phrases found in the document.")
        return

    print(f"Found {len(to_add)} new phrases to add.")
    for phrase in to_add:
        # Append new phrase to words.txt
        append_new_word_to_file(phrase)
        # Translate new phrase and add it to JSON with default weights
        translation = translate_word(phrase, translate_client)
        words_list.append({
            "portuguese": phrase,
            "english": translation,
            "weight_en_to_pt": 9,
            "weight_pt_to_en": 9
        })

    save_words(words_list)
    print("Successfully appended new phrases to words.txt and updated JSON")

def main():
    if "GOOGLE_TRANSLATE_APPLICATION_CREDENTIALS" not in os.environ:
        print("Error: GOOGLE_TRANSLATE_APPLICATION_CREDENTIALS environment variable not set.")
        sys.exit(1)

    choice = input("Update? (Y/n): ").strip().lower()
    words_list = load_words()

    english_first = ("-e" in sys.argv)
    translate_client = translate.Client()

    if choice in ("y", "yes", ""):
        update_from_doc(words_list, translate_client)

    # Read initial words from file
    initial_words = read_initial_words_from_file(WORDS_FILENAME)

    # Ensure translations for new words not yet in JSON
    for nw in initial_words:
        existing = find_word(words_list, nw)
        if existing is None:
            translation = translate_word(nw, translate_client)
            words_list.append({
                "portuguese": nw,
                "english": translation,
                "weight_en_to_pt": 9,
                "weight_pt_to_en": 9
            })

    save_words(words_list)
    print("Press Ctrl+C to exit.")
    print("Quiz starting...")

    try:
        while True:
            word_obj = weighted_random_choice(words_list, english_first)

            if english_first:
                # Show English first, guess Portuguese
                print("\nEnglish: ", word_obj["english"])
                input("Press Enter to see the Portuguese word...")
                print("Portuguese: ", word_obj["portuguese"])
            else:
                # Show Portuguese first, guess English
                print("\nPortuguese: ", word_obj["portuguese"])
                input("Press Enter to see the English translation...")
                print("English: ", word_obj["english"])

            while True:
                rating = input("How difficult was it? (0=Known, 9=Need to see more) [0-9]: ")
                if rating.isdigit() and 0 <= int(rating) <= 9:
                    rating = int(rating)
                    break
                else:
                    print("Please enter a valid number between 0 and 9.")

            # Update the appropriate weight based on mode
            if english_first:
                word_obj["weight_en_to_pt"] = rating
            else:
                word_obj["weight_pt_to_en"] = rating

            save_words(words_list)

    except KeyboardInterrupt:
        print("\nExiting...")
        save_words(words_list)

if __name__ == "__main__":
    main()