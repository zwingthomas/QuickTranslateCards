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
            return data.get("words", [])
    except (json.JSONDecodeError, FileNotFoundError):
        # If file is invalid JSON or can't be opened, create a new one
        data = {"words": []}
        with open(JSON_FILENAME, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return data["words"]

def save_words(words):
    data = {"words": words}
    with open(JSON_FILENAME, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def find_word(words_list, portuguese_word):
    for w in words_list:
        if w["portuguese"].lower() == portuguese_word.lower():
            return w
    return None

def translate_word(word, translate_client):
    # Translate from Portuguese (pt) to English (en)
    result = translate_client.translate(word, source_language='pt', target_language='en')
    return result['translatedText']

def weighted_random_choice(words_list):
    total_weight = sum(w["weight"] for w in words_list if w["weight"] > 0)
    if total_weight == 0:
        # If all weights are 0, just pick a random word
        return random.choice(words_list)
    r = random.uniform(0, total_weight)
    current = 0
    for w in words_list:
        current += w["weight"]
        if current >= r:
            return w
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
    # Appends a single word or phrase to words.txt if it doesn't exist
    # in the file already.
    # We'll just append to ensure no duplicates from doc.
    # You may want to check for duplicates in the file as well.
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

def update_from_doc(words_list):
    new_phrases = fetch_phrases_from_doc(DOCUMENT_ID)
    existing_portuguese = {w["portuguese"].lower() for w in words_list}
    to_add = [p for p in new_phrases if p.lower() not in existing_portuguese]

    if not to_add:
        print("No new phrases found in the document.")
        return

    print(f"Found {len(to_add)} new phrases to add.")
    for phrase in to_add:
        append_new_word_to_file(phrase)
    print("Successfully appended new phrases to words.txt")

def main():
    if "GOOGLE_TRANSLATE_APPLICATION_CREDENTIALS" not in os.environ:
        print("Error: GOOGLE_TRANSLATE_APPLICATION_CREDENTIALS environment variable not set.")
        sys.exit(1)

    choice = input("Update? (Y/n): ").strip().lower()
    words_list = load_words()

    if choice in ("y", "yes", ""):
        update_from_doc(words_list)

    english_first = ("-e" in sys.argv)
    translate_client = translate.Client()
    initial_words = read_initial_words_from_file(WORDS_FILENAME)

    # Ensure translations for new words
    for nw in initial_words:
        if find_word(words_list, nw) is None:
            translation = translate_word(nw, translate_client)
            words_list.append({
                "portuguese": nw,
                "english": translation,
                "weight": 9
            })

    save_words(words_list)
    print("Press Ctrl+C to exit.")
    print("Quiz starting...")

    try:
        while True:
            word_obj = weighted_random_choice(words_list)
            if english_first:
                print("\nEnglish: ", word_obj["english"])
                input("Press Enter to see the Portuguese word...")
                print("Portuguese: ", word_obj["portuguese"])
            else:
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

            word_obj["weight"] = rating
            save_words(words_list)
    except KeyboardInterrupt:
        print("\nExiting...")
        save_words(words_list)

if __name__ == "__main__":
    main()