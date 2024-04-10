import os
import json
import glob
from collections import OrderedDict

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def save_json(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def find_missing_items(original_items, newer_items):
    newer_item_ids = {item['id']: item for item in newer_items}
    missing_items = [item for item in original_items if item['id'] not in newer_item_ids]
    return missing_items

def remove_duplicate_entries(data):
    seen = OrderedDict()
    for entry in data:
        seen[entry['id']] = entry
    return list(seen.values())

def format_game_origin(source_file):
    base_filename = os.path.splitext(os.path.basename(source_file))[0]
    game_origin = base_filename[-5:]  # Extract the last 5 characters
    return game_origin

def merge_datasets(datatable_file, source_folder, output_folder):
    try:
        newest_data = load_json(datatable_file)
        newer_items = newest_data.get('items', [])
    except Exception as e:
        print(f"Error loading data from {datatable_file}: {e}")
        return []

    source_files = glob.glob(os.path.join(source_folder, '*.json'))

    # Reverse the order of source_files
    source_files.reverse()

    added_songs = []

    for source_file in source_files:
        try:
            original_data = load_json(source_file)
            original_items = original_data.get('items', [])
        except Exception as e:
            print(f"Error loading data from {source_file}: {e}")
            continue

        try:
            missing_items = find_missing_items(original_items, newer_items)
        except Exception as e:
            print(f"Error finding missing items: {e}")
            continue

        newer_items.extend(missing_items)

        for item in missing_items:
            added_songs.append({
                "id": item['id'],
                "uniqueId": item['uniqueId'],
                "sourceFile": os.path.basename(source_file)
            })

    newer_items.sort(key=lambda x: x.get('uniqueId', 0))

    newest_data['items'] = newer_items

    output_file_name = os.path.basename(datatable_file)
    output_file_path = os.path.join(output_folder, output_file_name)

    save_json(newest_data, output_file_path)

    added_ids = {item['id'] for item in added_songs}
    if added_ids:
        print(f"Added Entries to {output_file_name}:")
        for entry_id in added_ids:
            print(entry_id)

    return added_songs

def update_music_ai_section(datatable_folder):
    try:
        musicinfo_file = os.path.join(datatable_folder, 'musicinfo.json')
        music_ai_section_file = os.path.join(datatable_folder, 'music_ai_section.json')

        musicinfo_data = load_json(musicinfo_file)
        music_ai_section_data = load_json(music_ai_section_file)

        musicinfo_items = musicinfo_data.get('items', [])
        music_ai_section_items = music_ai_section_data.get('items', [])

        existing_entries = {(item['id'], item['uniqueId']) for item in music_ai_section_items}

        added_entries = []

        for musicinfo_item in musicinfo_items:
            item_id = musicinfo_item['id']
            unique_id = musicinfo_item['uniqueId']

            if (item_id, unique_id) not in existing_entries:
                new_entry = {
                    "id": item_id,
                    "uniqueId": unique_id,
                    "easy": 3 if musicinfo_item.get('starEasy', 0) < 6 else 5,
                    "normal": 3 if musicinfo_item.get('starNormal', 0) < 6 else 5,
                    "hard": 3 if musicinfo_item.get('starHard', 0) < 6 else 5,
                    "oni": 3 if musicinfo_item.get('starMania', 0) < 6 else 5,
                    "ura": 3 if musicinfo_item.get('starUra', 0) < 6 else 5,
                    "oniLevel11": "o" if musicinfo_item.get('starMania', 0) == 10 else "",
                    "uraLevel11": "o" if musicinfo_item.get('starUra', 0) == 10 else ""
                }

                music_ai_section_items.append(new_entry)
                added_entries.append((item_id, unique_id))
            else:
                existing_entry = next(
                    (item for item in music_ai_section_items if item['id'] == item_id and item['uniqueId'] == unique_id),
                    None
                )
                if existing_entry:
                    if 'oniLevel11' not in existing_entry:
                        existing_entry['oniLevel11'] = "o" if musicinfo_item.get('starMania', 0) == 10 else ""
                    if 'uraLevel11' not in existing_entry:
                        existing_entry['uraLevel11'] = "o" if musicinfo_item.get('starUra', 0) == 10 else ""

        music_ai_section_items.sort(key=lambda x: x.get('uniqueId', 0))

        music_ai_section_data['items'] = music_ai_section_items

        save_json(music_ai_section_data, music_ai_section_file)

        if added_entries:
            print("Added Entries to music_ai_section.json:")
            for item_id, unique_id in added_entries:
                print(f"ID: {item_id}, UniqueID: {unique_id}")

        return added_entries

    except Exception as e:
        print(f"Error updating music_ai_section.json: {e}")
        return []

def update_music_usbsetting(datatable_merged_folder):
    musicinfo_file_path = os.path.join(datatable_merged_folder, 'musicinfo.json')
    music_usbsetting_file_path = os.path.join(datatable_merged_folder, 'music_usbsetting.json')

    try:
        musicinfo_data = load_json(musicinfo_file_path)
        music_usbsetting_data = load_json(music_usbsetting_file_path)

        musicinfo_items = musicinfo_data.get('items', [])
        music_usbsetting_items = music_usbsetting_data.get('items', [])

        existing_entries = {(item['id'], item['uniqueId']) for item in music_usbsetting_items}

        added_entries = []

        for musicinfo_item in musicinfo_items:
            item_id = musicinfo_item['id']
            unique_id = musicinfo_item['uniqueId']

            if (item_id, unique_id) not in existing_entries:
                new_entry = {
                    "id": item_id,
                    "uniqueId": unique_id,
                    "usbVer": ""
                }

                music_usbsetting_items.append(new_entry)
                added_entries.append((item_id, unique_id))

        music_usbsetting_items.sort(key=lambda x: x.get('uniqueId', 0))

        music_usbsetting_data['items'] = music_usbsetting_items

        save_json(music_usbsetting_data, music_usbsetting_file_path)

        if added_entries:
            print("Added Entries to music_usbsetting.json:")
            for item_id, unique_id in added_entries:
                print(f"ID: {item_id}, UniqueID: {unique_id}")

        return added_entries

    except Exception as e:
        print(f"Error updating music_usbsetting.json: {e}")
        return []

if __name__ == "__main__":
    datatable_folder = 'datatable'
    source_folders = {
        'musicinfo': 'musicinfo',
        'music_order': 'music_order',
        'music_usbsetting': 'music_usbsetting',
        'music_attribute': 'music_attribute',
        'music_ai_section': 'music_ai_section'
    }
    output_folder = 'datatable_merged'
    added_songs_file = 'added_songs.json'

    os.makedirs(output_folder, exist_ok=True)

    all_added_songs = []

    for datatable_file, source_folder in source_folders.items():
        datatable_file_path = os.path.join(datatable_folder, f"{datatable_file}.json")

        added_songs = merge_datasets(datatable_file_path, source_folder, output_folder)
        all_added_songs.extend(added_songs)

    music_ai_section_added = update_music_ai_section(output_folder)
    music_usbsetting_added = update_music_usbsetting(output_folder)

    # Remove duplicate entries and format gameOrigin
    all_added_songs_unique = remove_duplicate_entries(all_added_songs)
    for entry in all_added_songs_unique:
        entry['gameOrigin'] = format_game_origin(entry['sourceFile'])
        del entry['sourceFile']

    save_json(all_added_songs_unique, os.path.join(added_songs_file))

    print(f"All added songs information saved to {added_songs_file}.")
