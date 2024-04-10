import os
import json

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def find_missing_items(original_items, newer_items):
    newer_item_ids = {item['id']: item for item in newer_items}
    missing_items = [item for item in original_items if item['id'] not in newer_item_ids]
    return missing_items

def remove_entries_with_keys(data, keys_to_remove):
    return [entry for entry in data if entry['key'] not in keys_to_remove]

def process_wordlist_files(wordlist_file, wordlist_folder, added_songs_file, output_folder):
    try:
        added_songs_data = load_json(added_songs_file)
    except Exception as e:
        print(f"Error loading added songs data: {e}")
        return

    try:
        wordlist_data = load_json(wordlist_file)
    except Exception as e:
        print(f"Error loading wordlist data: {e}")
        return

    for added_song in added_songs_data:
        song_id = added_song['id']
        game_origin = added_song['gameOrigin']

        # Generate keys to identify entries to remove in wordlist.json
        keys_to_remove = [
            f"song_sub_{song_id}",
            f"song_detail_{song_id}",
            f"song_{song_id}"
        ]

        # Remove entries from wordlist.json based on keys
        wordlist_data['items'] = remove_entries_with_keys(wordlist_data['items'], keys_to_remove)

        # Load and process wordlist_[gameOrigin].json
        wordlist_game_file = os.path.join(wordlist_folder, f"wordlist_{game_origin}.json")
        try:
            wordlist_game_data = load_json(wordlist_game_file)
        except Exception as e:
            print(f"Error loading wordlist game data ({game_origin}): {e}")
            continue

        # Copy entries from wordlist_game_data to wordlist_data
        for entry in wordlist_game_data['items']:
            if entry['key'] in keys_to_remove:
                wordlist_data['items'].append(entry)

    # Save modified wordlist data to output folder
    output_wordlist_file = os.path.join(output_folder, 'wordlist.json')
    save_json(wordlist_data, output_wordlist_file)
    print(f"Modified wordlist saved to: {output_wordlist_file}")

if __name__ == "__main__":
    datatable_folder = 'datatable'
    wordlist_folder = 'wordlist'
    added_songs_file = 'added_songs.json'
    output_folder = 'datatable_merged'

    os.makedirs(output_folder, exist_ok=True)

    wordlist_file = os.path.join(datatable_folder, 'wordlist.json')
    process_wordlist_files(wordlist_file, wordlist_folder, added_songs_file, output_folder)
