import json
import os
import random
import sys

from google.cloud import translate_v2 as translate

JSON_FILENAME = "words.json"
WORDS_FILENAME = "words.txt"

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
        sys.exit(1)

    words = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            w = line.strip()
            if w:
                words.append(w)
    return words

def main():
    # Check for credentials
    if "GOOGLE_TRANSLATE_APPLICATION_CREDENTIALS" not in os.environ:
        print("Error: GOOGLE_TRANSLATE_APPLICATION_CREDENTIALS environment variable not set.")
        print("Set this variable to the path of your service account JSON key file.")
        sys.exit(1)
    
    # Check if user wants English first
    english_first = ("-e" in sys.argv)

    # Create translate client
    translate_client = translate.Client()

    # Read initial words from file
    initial_words = read_initial_words_from_file(WORDS_FILENAME)

    words_list = load_words()

    # Ensure translations for new words
    for nw in initial_words:
        if find_word(words_list, nw) is None:
            # Not found, translate and add with default weight 9
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
            # Pick a random word according to weights
            word_obj = weighted_random_choice(words_list)

            # Show the words based on mode
            if english_first:
                # Show English first
                print("\nEnglish: ", word_obj["english"])
                input("Press Enter to see the Portuguese word...")
                print("Portuguese: ", word_obj["portuguese"])
            else:
                # Show Portuguese first
                print("\nPortuguese: ", word_obj["portuguese"])
                input("Press Enter to see the English translation...")
                print("English: ", word_obj["english"])

            # Ask user for difficulty rating
            while True:
                rating = input("How difficult was it? (0=Known, 9=Need to see more) [0-9]: ")
                if rating.isdigit() and 0 <= int(rating) <= 9:
                    rating = int(rating)
                    break
                else:
                    print("Please enter a valid number between 0 and 9.")

            # Update the weight
            word_obj["weight"] = rating
            save_words(words_list)

    except KeyboardInterrupt:
        print("\nExiting...")
        # Save before exit
        save_words(words_list)

if __name__ == "__main__":
    main()