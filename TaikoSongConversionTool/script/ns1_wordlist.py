import json

def merge_wordlists(file1_path, file2_path, output_path):
    # Load the contents of the first wordlist file
    with open(file1_path, 'r', encoding='utf-8') as file1:
        data1 = json.load(file1)

    # Load the contents of the second wordlist file
    with open(file2_path, 'r', encoding='utf-8') as file2:
        data2 = json.load(file2)

    # Define keys to remove from data1
    keys_to_remove_data1 = ["japaneseText", "chineseTText","chineseTFontType","koreanText","koreanFontType"]

    # Filter out entries from file 1 where key starts with "song_" and remove specific keys
    filtered_items_data1 = []
    for item in data1['items']:
        if not item['key'].startswith('song_'):
            # Remove specific keys from item
            filtered_item = {k: v for k, v in item.items() if k not in keys_to_remove_data1}
            filtered_items_data1.append(filtered_item)
    
# Define keys to remove from data2
    keys_to_remove_data2 = ["japaneseText", "japaneseFontType", "chineseTText","chineseTFontType","koreanText","koreanFontType"]

    for item2 in data2['items']:
        # Set englishUsFontType to 3
        item2['englishUsFontType'] = 0

        # Add missing translation fields using englishUsText from file 2
        languages = ['french', 'italian', 'german', 'spanish']
        for lang in languages:
            if lang + 'Text' not in item2:
                item2[lang + 'Text'] = item2['englishUsText']
                item2[lang + 'FontType'] = 3

    for item3 in data2['items']:
        if not item3['key'].startswith('song_detail_'):
            item3['englishUsFontType'] = 3
            
    # Filter out specific keys from entries in file 2
    filtered_items_data2 = []
    for item in data2['items']:
        # Remove specific keys from item
        filtered_item = {k: v for k, v in item.items() if k not in keys_to_remove_data2}
        filtered_items_data2.append(filtered_item)

    # Extend filtered data1 with filtered data2
    filtered_items_data1.extend(filtered_items_data2)

    # Update data1 with the merged and filtered items
    data1['items'] = filtered_items_data1

    # Save the updated JSON back to file
    with open(output_path, 'w', encoding='utf-8') as output_file:
        json.dump(data1, output_file, indent=4, ensure_ascii=False)

    print(f"Merged wordlists saved to '{output_path}'.")

# Example usage:
merge_wordlists('data\\_console\\NX\\datatable\\wordlist.json', 'out\\Data\\NX\\datatable\\wordlist.json', 'out\\Data\\NX\\datatable\\wordlist.json')

