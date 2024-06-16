import json

def merge_wordlists(file1_path, file2_path, output_path):
    # Load the contents of the first wordlist file
    with open(file1_path, 'r', encoding='utf-8') as file1:
        data1 = json.load(file1)

    # Load the contents of the second wordlist file
    with open(file2_path, 'r', encoding='utf-8') as file2:
        data2 = json.load(file2)

    # Filter out entries from file 1 where key starts with "song_"
    filtered_items = [item for item in data1['items'] if not item['key'].startswith('song_')]

    # Update entries from file 2 and add them to the filtered list
    for item2 in data2['items']:
        # Set englishUsFontType to 3
        item2['englishUsFontType'] = 3

        # Add missing translation fields using englishUsText from file 2
        languages = ['french', 'italian', 'german', 'spanish', 'chineseT', 'korean',
                     'portuguese', 'russian', 'turkish', 'arabic', 'dutch', 'chineseS']
        for lang in languages:
            if lang + 'Text' not in item2:
                item2[lang + 'Text'] = item2['englishUsText']
                item2[lang + 'FontType'] = 3

        # Add updated item from file 2 to the filtered list
        filtered_items.append(item2)

    # Update data1 with the merged and filtered items
    data1['items'] = filtered_items

    # Save the updated JSON back to file
    with open(output_path, 'w', encoding='utf-8') as output_file:
        json.dump(data1, output_file, indent=4, ensure_ascii=False)

    print(f"Merged wordlists saved to '{output_path}'.")

merge_wordlists('data\\_console\\Raw\\ReadAssets\\wordlist.json', 'out\\Data\\Raw\\ReadAssets\\wordlist.json', 'out\\Data\\Raw\\ReadAssets\\wordlist.json')

