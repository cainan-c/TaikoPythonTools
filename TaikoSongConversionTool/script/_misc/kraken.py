import os
import json

def process_folders(root_folder):
    data_entries = []
    
    for foldername in os.listdir(root_folder):
        folder_path = os.path.join(root_folder, foldername)
        if os.path.isdir(folder_path):
            process_subfolders(folder_path, data_entries)
    
    sorted_data_entries = sort_entries_by_id(data_entries)
    write_output_file(sorted_data_entries, root_folder)

def process_subfolders(folder_path, data_entries):
    for subdir, _, files in os.walk(folder_path):
        if 'data.json' in files:
            data_json_path = os.path.join(subdir, 'data.json')
            process_data_json(data_json_path, data_entries)

def process_data_json(data_json_path, data_entries):
    try:
        with open(data_json_path, 'r', encoding='utf-8') as data_file:
            data = json.load(data_file)
            id_value = data.get('id', '')  # Get 'id' value or default to empty string
            preview_pos = data.get('previewPos', 0)  # Get 'previewPos' value or default to 0
            data_entries.append({'id': id_value, 'previewPos': preview_pos})
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error reading {data_json_path}: {e}")

def sort_entries_by_id(data_entries):
    # Sort data_entries list by 'id' field
    sorted_entries = sorted(data_entries, key=lambda x: x['id'])
    return sorted_entries

def write_output_file(data_entries, root_folder):
    output_file_path = os.path.join(root_folder, 'output.json')
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(data_entries, output_file, indent=2)

if __name__ == '__main__':
    # Specify the root folder where you want to start processing
    root_folder = '.'  # Current directory where the script is executed
    process_folders(root_folder)
