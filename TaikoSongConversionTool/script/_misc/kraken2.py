import os
import json

def process_folders(root_folder):
    data_entries = []

    for foldername in os.listdir(root_folder):
        folder_path = os.path.join(root_folder, foldername)
        if os.path.isdir(folder_path):
            process_subfolders(folder_path, data_entries)
    
    write_output_file(data_entries, 'output_all.json', root_folder)

def process_subfolders(folder_path, data_entries):
    for subdir, _, files in os.walk(folder_path):
        if 'data.json' in files:
            data_json_path = os.path.join(subdir, 'data.json')
            process_data_json(data_json_path, data_entries)

def process_data_json(data_json_path, data_entries):
    try:
        with open(data_json_path, 'r', encoding='utf-8') as data_file:
            data = json.load(data_file)
            data_entry = {
                "id": data["id"],
                "songName": {
                    "jpText": data["songName"]["jpText"],
                    "jpFont": data["songName"]["jpFont"],
                    "enText": data["songName"]["enText"],
                    "enFont": data["songName"]["enFont"]
                },
                "songSubtitle": {
                    "jpText": data["songSubtitle"]["jpText"],
                    "jpFont": data["songSubtitle"]["jpFont"],
                    "enText": data["songSubtitle"]["enText"],
                    "enFont": data["songSubtitle"]["enFont"]
                },
                "songDetail": {
                    "jpText": data["songDetail"]["jpText"],
                    "jpFont": data["songDetail"]["jpFont"],
                    "enText": data["songDetail"]["enText"],
                    "enFont": data["songDetail"]["enFont"]
                }
            }
            data_entries.append(data_entry)
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
        print(f"Error reading {data_json_path}: {e}")

def write_output_file(data_entries, filename, root_folder):
    output_file_path = os.path.join(root_folder, filename)
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(data_entries, output_file, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    # Specify the root folder where you want to start processing
    root_folder = '.'  # Current directory where the script is executed
    process_folders(root_folder)
