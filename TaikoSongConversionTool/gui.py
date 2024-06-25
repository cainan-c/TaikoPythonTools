import concurrent.futures
import functools
import gzip
import json
import os
import random
import shutil
import subprocess
import tempfile
import tkinter as tk
import sv_ttk
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from tkinter import ttk, messagebox

selected_songs = set()
selected_song_ids = []

# Function to load configuration from file
def load_config():
    config_file = "config.json"
    default_config = {
        "max_concurrent": 5,  # Default value if not specified in config file
        "lang": "en",
        "custom_songs": False,
        "custom_song_path": "data_custom/"    
    }

    try:
        with open(config_file, "r") as f:
            config = json.load(f)
            # Override default values with values from config file
            default_config.update(config)
    except FileNotFoundError:
        print(f"Config file '{config_file}' not found. Using default configuration.")

    return default_config

data_dir = "data/"
musicinfo_path = os.path.join(data_dir, "datatable", "musicinfo.json")
wordlist_path = os.path.join(data_dir, "datatable", "wordlist.json")
previewpos_path = os.path.join(data_dir, "datatable", "previewpos.json")

# Load configuration
config = load_config()

custom_songs = config["custom_songs"]
lang = config["lang"]

if custom_songs == True:
    print("Custom Song Loading Enabled")
    custom_data_dir = config.get('custom_song_path')
    custom_musicinfo_path = os.path.join(custom_data_dir, "datatable", "musicinfo.json")
    custom_wordlist_path = os.path.join(custom_data_dir, "datatable", "wordlist.json")
    custom_previewpos_path = os.path.join(custom_data_dir, "datatable", "previewpos.json")

item_selection_state = {}

with open(musicinfo_path, "r", encoding="utf-8") as musicinfo_file:
    music_info = json.load(musicinfo_file)

with open(wordlist_path, "r", encoding="utf-8") as wordlist_file:
    word_list = json.load(wordlist_file)

if custom_songs == True:
    with open(custom_musicinfo_path, "r", encoding="utf-8") as custom_musicinfo_file:
        custom_music_info = json.load(custom_musicinfo_file)

    with open(custom_wordlist_path, "r", encoding="utf-8") as custom_wordlist_file:
        custom_word_list = json.load(custom_wordlist_file)

if lang == "jp":
    genre_map = {
        0: ("ポップス", "#219fbb"),
        1: ("アニメ", "#ff9700"),
        2: ("ボーカロイド", "#a2c4c8"),
        3: ("バラエティ", "#8fd321"),
        4: ("Unused", "#000000"),
        5: ("クラシック", "#d1a016"),
        6: ("ゲームミュージック", "#9c72c0"),
        7: ("ナムコオリジナル", "#ff5716"),
    }
else:
    genre_map = {
        0: ("Pop", "#219fbb"),
        1: ("Anime", "#ff9700"),
        2: ("Vocaloid", "#a2c4c8"),
        3: ("Variety", "#8fd321"),
        4: ("Unused (Kids)", "#000000"),
        5: ("Classic", "#d1a016"),
        6: ("Game Music", "#9c72c0"),
        7: ("Namco Original", "#ff5716"),
    } 

if lang == "jp":
    song_titles = {item["key"]: item["japaneseText"] for item in word_list["items"]}
    song_subtitles = {item["key"]: item["japaneseText"] for item in word_list["items"]}
else:
    song_titles = {item["key"]: item["englishUsText"] for item in word_list["items"]}
    song_subtitles = {item["key"]: item["englishUsText"] for item in word_list["items"]}

if custom_songs == True:
    if lang == "jp":
        custom_song_titles = {item["key"]: item["japaneseText"] for item in custom_word_list["items"]}
        custom_song_subtitles = {item["key"]: item["japaneseText"] for item in custom_word_list["items"]}
    else:
        custom_song_titles = {item["key"]: item["englishUsText"] for item in custom_word_list["items"]}
        custom_song_subtitles = {item["key"]: item["englishUsText"] for item in custom_word_list["items"]}

window = tk.Tk()
window.title("Taiko no Tatsujin Song Conversion GUI Tool")

window.iconbitmap('gui.ico')

# Set the initial size of the window
window.geometry("1400x800")  # Width x Height

# Create a new style for Treeview with grid lines
style = ttk.Style()
style.configure("Treeview", rowheight=25, borderwidth=1)
style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

# Use the new style for the Treeview
style.configure("Treeview.Heading", background="lightgrey", foreground="black", borderwidth=1)
style.map("Treeview.Heading", background=[('active', 'grey')])

sv_ttk.set_theme("dark")

# Create a frame to contain the Treeview and scrollbar
main_frame = ttk.Frame(window)
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Create Treeview and Scrollbar
tree = ttk.Treeview(main_frame, columns=("Select", "ID", "Song Name", "Song Subtitle", "Genre", "Difficulty"), show="headings", selectmode="extended")
if lang == "jp":
    tree.heading("Song Name", text="曲")
    tree.heading("Song Subtitle", text="曲名")
    tree.heading("Genre", text="ジャンル順")
    tree.heading("Difficulty", text="むずかしさ")
    tree.heading("Select", text="移動")
else:
    tree.heading("Song Name", text="Song Name")
    tree.heading("Song Subtitle", text="Song Subtitle")
    tree.heading("Genre", text="Genre")
    tree.heading("Difficulty", text="Difficulty")
    tree.heading("Select", text="Select")
tree.heading("ID", text="ID")


tree.column("Select", width=20, anchor=tk.CENTER)
tree.column("ID", width=60, anchor=tk.W)
tree.column("Song Name", anchor=tk.W)
tree.column("Song Subtitle", anchor=tk.W)
tree.column("Genre",  width=100, anchor=tk.W)
tree.column("Difficulty", width=120, anchor=tk.W)

vsb = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=vsb.set)

# Pack Treeview and Scrollbar into the main_frame
tree.pack(side="left", fill="both", expand=True)
vsb.pack(side="right", fill="y")

# Counter for selected items
selection_count = tk.IntVar()
selection_count.set(0)  # Initial selection count

def on_search_keyrelease(event):
    print("Key released:", event.keysym)
    #filter_treeview()

# Search Entry
if lang == "jp":
    search_label = tk.Label(window, text="フィルター曲：", anchor="w")
else:
    search_label = tk.Label(window, text="Filter Songs:", anchor="w")
search_label.pack(side="top", padx=20, pady=0, anchor="w")
search_var = tk.StringVar()
search_entry = ttk.Entry(window, textvariable=search_var)
search_entry.pack(side="bottom", fill="x", padx=10, pady=10)

def toggle_checkbox(event):
    selected_items = tree.selection()
    for item_id in selected_items:
        values = list(tree.item(item_id, "values"))
        song_id = values[1]  # Ensure this points to the correct column for song ID

        if values[0] == "☐":
            values[0] = "☑"
            if song_id not in selected_song_ids:
                selected_song_ids.append(song_id)
                selection_count.set(selection_count.get() + 1)
        else:
            values[0] = "☐"
            if song_id in selected_song_ids:
                selected_song_ids.remove(song_id)
                selection_count.set(selection_count.get() - 1)

        tree.item(item_id, values=values)
    
    update_selection_count()
    return "break"

def filter_treeview():
    search_text = search_var.get().strip().lower()
    populate_tree(search_text)  # Populate Treeview with filtered data
    
def populate_tree(search_text=""):
    # Clear existing items in the Treeview
    tree.delete(*tree.get_children())

    def add_song_to_tree(song, title_dict, subtitle_dict):
        song_id = f"{song['id']}"
        genre_no = song["genreNo"]
        genre_name, genre_color = genre_map.get(genre_no, ("Unknown Genre", "white"))
        english_title = title_dict.get(f"song_{song_id}", "-")
        english_subtitle = subtitle_dict.get(f"song_sub_{song_id}", "-")

        star_easy = song.get("starEasy", "N/A")
        star_normal = song.get("starNormal", "N/A")
        star_hard = song.get("starHard", "N/A")
        star_mania = song.get("starMania", "N/A")
        star_ura = song.get("starUra", 0)

        difficulty_info_parts = [
            f"★{star_easy}",
            f"★{star_normal}",
            f"★{star_hard}",
            f"★{star_mania}",
        ]

        if star_ura > 0:
            difficulty_info_parts.append(f"★{star_ura}")

        difficulty_info = " | ".join(difficulty_info_parts)

        # Check if the search text matches the song name
        if search_text in english_title.lower():
            values = ["☐", song_id, english_title, english_subtitle, genre_name, difficulty_info]
            if song_id in selected_song_ids:
                values[0] = "☑"
            item_id = tree.insert("", "end", values=values, tags=(genre_name,))
            tree.tag_configure(genre_name, background=genre_color)
            # Re-select item if it was previously selected
            if song_id in selected_song_ids:
                tree.selection_add(item_id)

    for song in sorted(music_info["items"], key=lambda x: x["id"]):  # Sort by ID
        add_song_to_tree(song, song_titles, song_subtitles)

    if custom_songs:
        for song in sorted(custom_music_info["items"], key=lambda x: x["id"]):  # Sort by ID
            add_song_to_tree(song, custom_song_titles, custom_song_subtitles)

search_entry.bind("<KeyRelease>", lambda event: filter_treeview())

def sort_tree(sort_option):
    # Clear existing items in the Treeview
    tree.delete(*tree.get_children())

    def add_sorted_songs(sorted_songs, title_dict, subtitle_dict):
        for song in sorted_songs:
            song_id = f"{song['id']}"
            genre_no = song["genreNo"]
            genre_name, genre_color = genre_map.get(genre_no, ("Unknown Genre", "white"))
            english_title = title_dict.get(f"song_{song_id}", "-")
            english_subtitle = subtitle_dict.get(f"song_sub_{song_id}", "-")

            star_easy = song.get("starEasy", "N/A")
            star_normal = song.get("starNormal", "N/A")
            star_hard = song.get("starHard", "N/A")
            star_mania = song.get("starMania", "N/A")
            star_ura = song.get("starUra", 0)

            difficulty_info_parts = [
                f"★{star_easy}",
                f"★{star_normal}",
                f"★{star_hard}",
                f"★{star_mania}",
            ]

            if star_ura > 0:
                difficulty_info_parts.append(f"★{star_ura}")

            difficulty_info = " | ".join(difficulty_info_parts)

            values = ["☐", song_id, english_title, english_subtitle, genre_name, difficulty_info]
            if song_id in selected_song_ids:
                values[0] = "☑"
            item_id = tree.insert("", "end", values=values, tags=(genre_name,))
            tree.tag_configure(genre_name, background=genre_color)
            # Re-select item if it was previously selected
            if song_id in selected_song_ids:
                tree.selection_add(item_id)

    if sort_option == "ID":
        sorted_songs = sorted(music_info["items"], key=lambda x: x["id"])
        add_sorted_songs(sorted_songs, song_titles, song_subtitles)
        if custom_songs:
            sorted_custom_songs = sorted(custom_music_info["items"], key=lambda x: x["id"])
            add_sorted_songs(sorted_custom_songs, custom_song_titles, custom_song_subtitles)
    elif sort_option == "Song Name":
        sorted_songs = sorted(music_info["items"], key=lambda x: song_titles.get(f"song_{x['id']}", "-"))
        add_sorted_songs(sorted_songs, song_titles, song_subtitles)
        if custom_songs:
            sorted_custom_songs = sorted(custom_music_info["items"], key=lambda x: custom_song_titles.get(f"song_{x['id']}", "-"))
            add_sorted_songs(sorted_custom_songs, custom_song_titles, custom_song_subtitles)
    elif sort_option == "Genre":
        for genre_no in sorted(genre_map.keys()):
            sorted_songs = [song for song in music_info["items"] if song["genreNo"] == genre_no]
            add_sorted_songs(sorted_songs, song_titles, song_subtitles)
            if custom_songs:
                sorted_custom_songs = [song for song in custom_music_info["items"] if song["genreNo"] == genre_no]
                add_sorted_songs(sorted_custom_songs, custom_song_titles, custom_song_subtitles)


def populate_song_entry(song):
    #unique_id = ""
    song_id = f"{song['id']}"
    genre_no = song["genreNo"]
    genre_name, genre_color = genre_map.get(genre_no, ("Unknown Genre", "white"))
    english_title = song_titles.get(f"song_{song_id}", "-")
    english_subtitle = song_subtitles.get(f"song_sub_{song_id}", "-")
    if custom_songs == True:
        english_title = custom_song_titles.get(f"song_{song_id}", "-")
        english_subtitle = custom_song_subtitles.get(f"song_sub_{song_id}", "-")        

    star_easy = song.get("starEasy", "N/A")
    star_normal = song.get("starNormal", "N/A")
    star_hard = song.get("starHard", "N/A")
    star_mania = song.get("starMania", "N/A")
    star_ura = song.get("starUra", 0)

    difficulty_info_parts = [
        f"{star_easy}",
        f"{star_normal}",
        f"{star_hard}",
        f"{star_mania}",
    ]

    if star_ura > 0:
        difficulty_info_parts.append(f"{star_ura}")

    difficulty_info = " | ".join(difficulty_info_parts)

    tree.insert("", "end", values=("☐", song_id, english_title, english_subtitle, genre_name, difficulty_info))
    tree.tag_configure(genre_name, background=genre_color)

# Populate the Treeview initially
populate_tree()

def update_selection_count(event=None):
    selected_items = tree.selection()
    count_selected = selection_count.get()  # Retrieve the value of selection_count

    platform = game_platform_var.get()
    if platform == "PS4":
        max_entries = 400
    elif platform == "NS1":
        max_entries = 600
    elif platform == "PTB":
        max_entries = 200
    else:
        max_entries = 0

    if len(selected_items) > max_entries:
        messagebox.showerror("Selection Limit Exceeded", f"Maximum {max_entries} entries can be selected for {platform}.")
    else:
        # Update the selection count label text
        selection_count_label.config(text=f"{count_selected}/{max_entries}")

# Bind the treeview selection event to update_selection_count function
tree.bind("<<TreeviewSelect>>", update_selection_count)

# Bind Treeview click event to toggle item selection
#tree.bind("<Button-1>", lambda event: toggle_selection(tree.identify_row(event.y)))
tree.bind("<ButtonRelease-1>", toggle_checkbox)
#tree.bind("<Button-1>", on_treeview_click)

def preview_audio(song_id):
    preview_pos = get_preview_pos(song_id)
    if preview_pos is not None:
        song_filename = os.path.join(data_dir, "sound", f"song_{song_id}.mp3")
        subprocess.run(["ffplay", "-autoexit", "-ss", f"{preview_pos / 1000}", song_filename])

    if custom_songs:
        custom_preview_pos = get_preview_pos(song_id)
        if custom_preview_pos is not None:
            custom_song_filename = os.path.join(custom_data_dir, "sound", f"song_{song_id}.mp3")
            subprocess.run(["ffplay", "-autoexit", "-ss", f"{custom_preview_pos / 1000}", custom_song_filename])

def get_preview_pos(song_id):
    with open(previewpos_path, "r", encoding="utf-8") as previewpos_file:
        previewpos_data = json.load(previewpos_file)
        for item in previewpos_data:
            if item["id"] == song_id:
                return item["previewPos"]
    
    if custom_songs:
        with open(custom_previewpos_path, "r", encoding="utf-8") as custom_previewpos_file:
            custom_previewpos_data = json.load(custom_previewpos_file)
            for item in custom_previewpos_data:
                if item["id"] == song_id:
                    return item["previewPos"]
    return None

def preview_selected():
    selected_item = tree.selection()
    if selected_item:
        song_id = tree.item(selected_item[0])["values"][1]  # Ensure this points to the correct column for song ID
        preview_audio(song_id)

def merge_ptb(file1_path, file2_path, output_path):
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

def encrypt_file_ptb_audio(input_file, output_file, key, iv):
    with open(input_file, 'rb') as f_in:
        data = f_in.read()

    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    padded_data = data + b'\0' * (16 - len(data) % 16)  # Pad the data to make it a multiple of block size
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Write IV followed by encrypted data to output file
    with open(output_file, 'wb') as f_out:
        f_out.write(iv)
        f_out.write(encrypted_data)

# audio conversion stuff(ptb)
def create_and_encrypt_acb(input_audio, song_id):
    # Generate a unique random temporary folder name
    with tempfile.TemporaryDirectory(prefix='song_') as temp_folder:
        try:
            # Convert input audio to 44100Hz WAV
            temp_wav_file = os.path.join(temp_folder, f'input_{song_id}.wav')

            audio = AudioSegment.from_file(input_audio)
            audio = audio.set_frame_rate(44100)
            audio.export(temp_wav_file, format='wav')

            # Generate .hca file using VGAudioCli.exe
            hca_folder = os.path.join(temp_folder, f'song_{song_id}')
            os.makedirs(hca_folder, exist_ok=True)
            hca_file = os.path.join(hca_folder, '00000.hca')
            subprocess.run(['data/_resource/executable/VGAudioCli.exe', temp_wav_file, hca_file], check=True)

            # Copy sample .acb template to temporary location
            acb_template = 'data/_resource/templates/song_sample.acb'
            temp_acb_file = os.path.join(temp_folder, f'song_{song_id}.acb')
            shutil.copy(acb_template, temp_acb_file)

            # Edit .acb using ACBEditor
            subprocess.run(['data/_resource/executable/ACBEditor.exe', hca_folder], check=True)

            # Encrypt .acb file to .bin with IV prepended
            key = bytes.fromhex('54704643596B474170554B6D487A597A')
            iv = bytes([0xFF] * 16)
            encrypted_bin_file = os.path.join(temp_folder, f'song_{song_id}.bin')
            encrypt_file_ptb_audio(temp_acb_file, encrypted_bin_file, key, iv)

            # Move encrypted .bin file to the root folder
            final_bin_file = f'song_{song_id}.bin'
            shutil.move(encrypted_bin_file, final_bin_file)

        except Exception as e:
            print(f"Error: {e}")

def merge_ps4_int(file1_path, file2_path, output_path):
    # Load the contents of the first wordlist file
    with open(file1_path, 'r', encoding='utf-8') as file1:
        data1 = json.load(file1)

    # Load the contents of the second wordlist file
    with open(file2_path, 'r', encoding='utf-8') as file2:
        data2 = json.load(file2)

    # Define keys to remove from data1, for space saving reasons. (sorry south americans)
    keys_to_remove_data1 = ["neutralSpanishText","neutralSpanishFontType","brazilPortugueseText","brazilPortugueseFontType"]

    # Filter out entries from file 1 where key starts with "song_" and remove specific keys
    filtered_items_data1 = []
    for item in data1['items']:
        if not item['key'].startswith('song_'):
            # Remove specific keys from item
            filtered_item = {k: v for k, v in item.items() if k not in keys_to_remove_data1}
            #filtered_items = [item for item in data1['items'] if not item['key'].startswith('song_')]
            filtered_items_data1.append(filtered_item)

    # Define keys to remove from data2
    keys_to_remove_data2 = ["japaneseText", "japaneseFontType", "chineseTText","chineseTFontType","koreanText","koreanFontType"]

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

def merge_ps4_jp(file1_path, file2_path, output_path):
    # Load the contents of the first wordlist file
    with open(file1_path, 'r', encoding='utf-8') as file1:
        data1 = json.load(file1)

    # Load the contents of the second wordlist file
    with open(file2_path, 'r', encoding='utf-8') as file2:
        data2 = json.load(file2)

    # Define keys to remove from data1
    keys_to_remove_data1 = ["frenchText", "frenchFontType", "italianText", "italianFontType", "germanText", "germanFontType", "spanishText", "spanishFontType","neutralSpanishText","neutralSpanishFontType","brazilPortugueseText","brazilPortugueseFontType"]

    # Filter out entries from file 1 where key starts with "song_" and remove specific keys
    filtered_items_data1 = []
    for item in data1['items']:
        if not item['key'].startswith('song_'):
            # Remove specific keys from item
            filtered_item = {k: v for k, v in item.items() if k not in keys_to_remove_data1}
            filtered_items_data1.append(filtered_item)

    # Define keys to remove from data2
    keys_to_remove_data2 = [""]

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

def merge_ns1_int(file1_path, file2_path, output_path):
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

def merge_ns1_jp(file1_path, file2_path, output_path):
    # Load the contents of the first wordlist file
    with open(file1_path, 'r', encoding='utf-8') as file1:
        data1 = json.load(file1)

    # Load the contents of the second wordlist file
    with open(file2_path, 'r', encoding='utf-8') as file2:
        data2 = json.load(file2)

    # Define keys to remove from data1
    keys_to_remove_data1 = ["frenchText", "frenchFontType", "italianText", "italianFontType", "germanText", "germanFontType", "spanishText", "spanishFontType"]

    # Filter out entries from file 1 where key starts with "song_" and remove specific keys
    filtered_items_data1 = []
    for item in data1['items']:
        if not item['key'].startswith('song_'):
            # Remove specific keys from item
            filtered_item = {k: v for k, v in item.items() if k not in keys_to_remove_data1}
            filtered_items_data1.append(filtered_item)
    
    # Define keys to remove from data2
    keys_to_remove_data2 = ["japaneseFontType"]

    for item2 in data2['items']:
        # Set englishUsFontType to 3
        item2['englishUsFontType'] = 0

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

# audio conversion stuff(ns1/ps4)
#from idsp.py
def convert_audio_to_idsp(input_file, output_file):
    temp_folder = tempfile.mkdtemp()
    try:
        if not input_file.lower().endswith('.wav'):
            temp_wav_file = os.path.join(temp_folder, "temp.wav")
            audio = AudioSegment.from_file(input_file)
            audio.export(temp_wav_file, format="wav")
            input_file = temp_wav_file

        vgaudio_cli_path = os.path.join("data/_resource/executable", "VGAudioCli.exe")
        subprocess.run([vgaudio_cli_path, "-i", input_file, "-o", output_file], check=True)
    finally:
        shutil.rmtree(temp_folder, ignore_errors=True)

#from lopus.py
def convert_audio_to_opus(input_file, output_file):
    # Create a unique temporary folder to store intermediate files
    temp_folder = tempfile.mkdtemp()

    try:
        # Check if the input file is already in WAV format
        if not input_file.lower().endswith('.wav'):
            # Load the input audio file using pydub and convert to WAV
            temp_wav_file = os.path.join(temp_folder, "temp.wav")
            audio = AudioSegment.from_file(input_file)
            audio = audio.set_frame_rate(48000)  # Set frame rate to 48000 Hz
            audio.export(temp_wav_file, format="wav")
            input_file = temp_wav_file

        # Path to VGAudioCli executable
        vgaudio_cli_path = os.path.join("data/_resource/executable", "VGAudioCli.exe")

        # Run VGAudioCli to convert WAV to Switch OPUS
        subprocess.run([vgaudio_cli_path, "-i", input_file, "-o", output_file, "--opusheader", "namco"], check=True)

    finally:
        # Clean up temporary folder
        shutil.rmtree(temp_folder, ignore_errors=True)

#from wav.py
def convert_audio_to_wav(input_file, output_file):
    try:
        # Load the input audio file using pydub
        audio = AudioSegment.from_file(input_file)

        # Ensure the output file has a .wav extension
        if not output_file.lower().endswith('.wav'):
            output_file += '.wav'

        # Export the audio to WAV format
        audio.export(output_file, format="wav")

    except Exception as e:
        raise RuntimeError(f"Error during WAV conversion: {e}")

#from at9.py
def convert_audio_to_at9(input_file, output_file):
    # Create a unique temporary folder to store intermediate files
    temp_folder = tempfile.mkdtemp()
    
    try:
        # Check if the input file is already in WAV format
        if not input_file.lower().endswith('.wav'):
            # Load the input audio file using pydub and convert to WAV
            temp_wav_file = os.path.join(temp_folder, "temp.wav")
            audio = AudioSegment.from_file(input_file)
            audio.export(temp_wav_file, format="wav")
            input_file = temp_wav_file

        # Path to AT9Tool executable
        at9tool_cli_path = os.path.join("data/_resource/executable", "at9tool.exe")

        # Run VGAudioCli to convert WAV to AT9
        subprocess.run([at9tool_cli_path, "-e", "-br", "192", input_file, output_file], check=True)

    finally:
        # Clean up temporary folder
        shutil.rmtree(temp_folder, ignore_errors=True)

# from bnsf.py
def convert_to_mono_48k(input_file, output_file):
    """Convert input audio file to 16-bit mono WAV with 48000 Hz sample rate."""
    try:
        audio = AudioSegment.from_file(input_file)
        audio = audio.set_channels(1)  # Convert to mono
        audio = audio.set_frame_rate(48000)  # Set frame rate to 48000 Hz
        audio = audio.set_sample_width(2)  # Set sample width to 16-bit (2 bytes)
        audio.export(output_file, format='wav')
    except CouldntDecodeError:
        print(f"Error: Unable to decode {input_file}. Please provide a valid audio file.")
        #sys.exit(1)

def run_encode_tool(input_wav, output_bs):
    """Run external encode tool with specified arguments."""
    subprocess.run(['data/_resource/executable/encode.exe', '0', input_wav, output_bs, '48000', '14000'])

def modify_bnsf_template(output_bs, output_bnsf, header_size, total_samples):
    """Modify the BNSF template file with calculated values and combine with output.bs."""
    # Calculate the file size of output.bs
    bs_file_size = os.path.getsize(output_bs)

    # Create modified BNSF data
    new_file_size = bs_file_size + header_size - 0x8
    total_samples_bytes = total_samples.to_bytes(4, 'big')
    bs_file_size_bytes = bs_file_size.to_bytes(4, 'big')
    
    # Read BNSF template data
    with open('data/_resource/templates/header.bnsf', 'rb') as template_file:
        bnsf_template_data = bytearray(template_file.read())

    # Modify BNSF template with calculated values
    bnsf_template_data[0x4:0x8] = new_file_size.to_bytes(4, 'big')  # File size
    bnsf_template_data[0x1C:0x20] = total_samples_bytes  # Total sample count
    bnsf_template_data[0x2C:0x30] = bs_file_size_bytes  # Size of output.bs

    # Append output.bs data to modified BNSF template
    with open(output_bs, 'rb') as bs_file:
        bs_data = bs_file.read()
        final_bnsf_data = bnsf_template_data + bs_data

    # Write final BNSF file
    with open(output_bnsf, 'wb') as output_file:
        output_file.write(final_bnsf_data)

#from nus3.py
def generate_random_uint16_hex():
    return format(random.randint(0, 65535), '04X')

def select_template_name(game, output_file):
    base_filename = os.path.splitext(output_file)[0]
    length = len(base_filename)

    if game == "nijiiro":
        if length == 8:
            return "song_ABC"
        elif length == 9:
            return "song_ABCD"
        elif length == 10:
            return "song_ABCDE"
        elif length == 11:
            return "song_ABCDEF"
        elif length == 12:
            return "song_ABCDEFG"    
        elif length == 13:
            return "song_ABCDEFGH"
    elif game == "ps4":
        if length == 8:
            return "song_ABC"
        elif length == 9:
            return "song_ABCD"
        elif length == 10:
            return "song_ABCDE"
        elif length == 11:
            return "song_ABCDEF"
    elif game == "ns1":
        if length == 8:
            return "song_ABC"
        elif length == 9:
            return "song_ABCD"
        elif length == 10:
            return "song_ABCDE"
        elif length == 11:
            return "song_ABCDEF"
    elif game == "wiiu3":
        if length == 8:
            return "song_ABC"
        elif length == 9:
            return "song_ABCD"
        elif length == 10:
            return "song_ABCDE"
        elif length == 11:
            return "song_ABCDEF"

    raise ValueError("Unsupported game or output file name length.")

def modify_nus3bank_template(game, template_name, audio_file, preview_point, output_file):
    game_templates = {        
        "nijiiro": {
            "template_folder": "nijiiro",
            "templates": {
                "song_ABC": {
                    "unique_id_offset": 176,
                    "audio_size_offsets": [76, 1568, 1852],
                    "preview_point_offset": 1724,
                    "song_placeholder": "song_ABC",
                    "template_file": "song_ABC.nus3bank"
                },
                "song_ABCD": {
                    "unique_id_offset": 176,
                    "audio_size_offsets": [76, 1568, 1852],
                    "preview_point_offset": 1724,
                    "song_placeholder": "song_ABCD",
                    "template_file": "song_ABCD.nus3bank"
                },
                "song_ABCDE": {
                    "unique_id_offset": 176,
                    "audio_size_offsets": [76, 1568, 1852],
                    "preview_point_offset": 1724,
                    "song_placeholder": "song_ABCDE",
                    "template_file": "song_ABCDE.nus3bank"
                },
                "song_ABCDEF": {
                    "unique_id_offset": 180,
                    "audio_size_offsets": [76, 1576, 1868],
                    "preview_point_offset": 1732,
                    "song_placeholder": "song_ABCDEF",
                    "template_file": "song_ABCDEF.nus3bank"
                },
                "song_ABCDEFG": {
                    "unique_id_offset": 180,
                    "audio_size_offsets": [76, 1672, 1964],
                    "preview_point_offset": 1824,
                    "song_placeholder": "song_ABCDEFG",
                    "template_file": "song_ABCDEFG.nus3bank"
                },
                "song_ABCDEFGH": {
                    "unique_id_offset": 180,
                    "audio_size_offsets": [76, 1576, 1868],
                    "preview_point_offset": 1732,
                    "song_placeholder": "song_ABCDEFGH",
                    "template_file": "song_ABCDEFGH.nus3bank"
                },            
            }
        },
        "ns1": {
            "template_folder": "ns1",
            "templates": {
                "song_ABC": {
                    "audio_size_offsets": [76, 5200, 5420],
                    "preview_point_offset": 5324,
                    "song_placeholder": "SONG_ABC",
                    "template_file": "SONG_ABC.nus3bank"
                },
                "song_ABCD": {
                    "audio_size_offsets": [76, 5200, 5420],
                    "preview_point_offset": 5324,
                    "song_placeholder": "SONG_ABCD",
                    "template_file": "SONG_ABCD.nus3bank"
                },
                "song_ABCDE": {
                    "audio_size_offsets": [76, 5200, 5404],
                    "preview_point_offset": 5320,
                    "song_placeholder": "SONG_ABCDE",
                    "template_file": "SONG_ABCDE.nus3bank"
                },
                "song_ABCDEF": {
                    "audio_size_offsets": [76, 5208, 5420],
                    "preview_point_offset": 5324,
                    "song_placeholder": "SONG_ABCDEF",
                    "template_file": "SONG_ABCDEF.nus3bank"
                }
            }
        },
        "ps4": {
            "template_folder": "ps4",
            "templates": {
                "song_ABC": {
                    "audio_size_offsets": [76, 3220, 3436],
                    "preview_point_offset": 3344,
                    "song_placeholder": "SONG_ABC",
                    "template_file": "SONG_ABC.nus3bank"
                },
                "song_ABCD": {
                    "audio_size_offsets": [76, 3220, 3436],
                    "preview_point_offset": 3344,
                    "song_placeholder": "SONG_ABCD",
                    "template_file": "SONG_ABCD.nus3bank"
                },
                "song_ABCDE": {
                    "audio_size_offsets": [76, 3220, 3436],
                    "preview_point_offset": 3344,
                    "song_placeholder": "SONG_ABCDE",
                    "template_file": "SONG_ABCDE.nus3bank"
                },
                "song_ABCDEF": {
                    "audio_size_offsets": [76, 3228, 3452],
                    "preview_point_offset": 3352,
                    "song_placeholder": "SONG_ABCDEF",
                    "template_file": "SONG_ABCDEF.nus3bank"
                }
            }
        },
        "wiiu3": {
            "template_folder": "wiiu3",
            "templates": {
                "song_ABC": {
                    "audio_size_offsets": [76, 3420, 3612],
                    "preview_point_offset": 3540,
                    "song_placeholder": "SONG_ABC",
                    "template_file": "SONG_ABC.nus3bank"
                },
                "song_ABCD": {
                    "audio_size_offsets": [76, 3420, 3612],
                    "preview_point_offset": 3540,
                    "song_placeholder": "SONG_ABCD",
                    "template_file": "SONG_ABCD.nus3bank"
                },
                "song_ABCDE": {
                    "audio_size_offsets": [76, 3420, 3612],
                    "preview_point_offset": 3540,
                    "song_placeholder": "SONG_ABCDE",
                    "template_file": "SONG_ABCDE.nus3bank"
                },
                "song_ABCDEF": {
                    "audio_size_offsets": [76, 3428, 3612],
                    "preview_point_offset": 3548,
                    "song_placeholder": "SONG_ABCDEF",
                    "template_file": "SONG_ABCDEF.nus3bank"
                }
            }
        },
    }

    if game not in game_templates:
        raise ValueError("Unsupported game.")

    templates_config = game_templates[game]

    if template_name not in templates_config["templates"]:
        raise ValueError(f"Unsupported template for {game}.")

    template_config = templates_config["templates"][template_name]
    template_folder = templates_config["template_folder"]

    # Read template nus3bank file from the specified game's template folder
    template_file = os.path.join("data/_resource/templates", template_folder, template_config['template_file'])
    with open(template_file, 'rb') as f:
        template_data = bytearray(f.read())

    # Set unique ID if it exists in the template configuration
    if 'unique_id_offset' in template_config:
        # Generate random UInt16 hex for unique ID
        unique_id_hex = generate_random_uint16_hex()
        # Set unique ID in the template data at the specified offset
        template_data[template_config['unique_id_offset']:template_config['unique_id_offset']+2] = bytes.fromhex(unique_id_hex)

    # Get size of the audio file in bytes
    audio_size = os.path.getsize(audio_file)

    # Convert audio size to UInt32 bytes in little-endian format
    size_bytes = audio_size.to_bytes(4, 'little')

    # Set audio size in the template data at the specified offsets
    for offset in template_config['audio_size_offsets']:
        template_data[offset:offset+4] = size_bytes

    # Convert preview point (milliseconds) to UInt32 bytes in little-endian format
    preview_point_ms = int(preview_point)
    preview_point_bytes = preview_point_ms.to_bytes(4, 'little')

    # Set preview point in the template data at the specified offset
    template_data[template_config['preview_point_offset']:template_config['preview_point_offset']+4] = preview_point_bytes

    # Replace song name placeholder with the output file name in bytes
    output_file_bytes = output_file.encode('utf-8')
    template_data = template_data.replace(template_config['song_placeholder'].encode('utf-8'), output_file_bytes.replace(b'.nus3bank', b''))

    # Append the audio file contents to the modified template data
    with open(audio_file, 'rb') as audio:
        template_data += audio.read()

    # Write the modified data to the output file
    with open(output_file, 'wb') as out:
        out.write(template_data)

    print(f"Created {output_file} successfully.")

def run_script(script_name, script_args):
    if script_name == "idsp":
        input_file, output_file = script_args
        convert_audio_to_idsp(input_file, output_file)
    elif script_name == "lopus":
        input_file, output_file = script_args
        convert_audio_to_opus(input_file, output_file)
    elif script_name == "at9":
        input_file, output_file = script_args
        convert_audio_to_at9(input_file, output_file)        
    elif script_name == "wav":
        input_file, output_file = script_args
        convert_audio_to_wav(input_file, output_file)              
    elif script_name == "bnsf":
        input_audio, output_bnsf = script_args
        temp_folder = 'temp'
        os.makedirs(temp_folder, exist_ok=True)
        output_wav = os.path.join(temp_folder, 'output_mono.wav')
        output_bs = os.path.join(temp_folder, 'output.bs')
        header_size = 0x30
        
        try:
            convert_to_mono_48k(input_audio, output_wav)
            run_encode_tool(output_wav, output_bs)
            mono_wav = AudioSegment.from_wav(output_wav)
            total_samples = len(mono_wav.get_array_of_samples())
            modify_bnsf_template(output_bs, output_bnsf, header_size, total_samples)
            print("BNSF file created:", output_bnsf)
        finally:
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder)    
    elif script_name == "nus3":
        game, audio_file, preview_point, output_file = script_args
        template_name = select_template_name(game, output_file)
        modify_nus3bank_template(game, template_name, audio_file, preview_point, output_file)
    else:
        print(f"Unsupported script: {script_name}")
        #sys.exit(1)

def convert_audio_to_nus3bank(input_audio, audio_type, game, preview_point, song_id):
    output_filename = f"song_{song_id}.nus3bank"
    converted_audio_file = f"{input_audio}.{audio_type}"

    if audio_type in ["bnsf", "at9", "idsp", "lopus", "wav"]:
        try:
            run_script(audio_type, [input_audio, converted_audio_file])
            run_script("nus3", [game, converted_audio_file, preview_point, output_filename])
            print(f"Conversion successful! Created {output_filename}")

            if os.path.exists(converted_audio_file):
                os.remove(converted_audio_file)
                print(f"Deleted {converted_audio_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
    else:
        print(f"Unsupported audio type: {audio_type}")


# file encryption
def encrypt_file_ptb(input_file, output_file):
    # Generate a random initialization vector (IV)
    iv = os.urandom(16)  # AES block size is 16 bytes

    # Pad the key if necessary (AES-128 requires a 16-byte key)
    key = bytes.fromhex("54704643596B474170554B6D487A597A")

    # Create an AES CBC cipher with the given key and IV
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    with open(input_file, 'rb') as f_in:
        with open(output_file, 'wb') as f_out:
            # Write the IV to the output file (needed for decryption)
            f_out.write(iv)

            # Encrypt the file chunk by chunk
            while True:
                chunk = f_in.read(16)  # Read 16 bytes at a time
                if len(chunk) == 0:
                    break
                elif len(chunk) % 16 != 0:
                    # Add padding to the last block if needed
                    padder = padding.PKCS7(128).padder()
                    padded_data = padder.update(chunk) + padder.finalize()
                    chunk = padded_data
                encrypted_chunk = encryptor.update(chunk)
                f_out.write(encrypted_chunk)

            # Finalize the encryption (encryptor might have remaining data)
            final_chunk = encryptor.finalize()
            f_out.write(final_chunk)

def encrypt_file_ns1(input_file, output_file):
    # Generate a random initialization vector (IV)
    iv = os.urandom(16)  # AES block size is 16 bytes

    # Pad the key if necessary (AES-128 requires a 16-byte key)
    key = bytes.fromhex("566342346438526962324A366334394B")

    # Create an AES CBC cipher with the given key and IV
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    with open(input_file, 'rb') as f_in:
        with open(output_file, 'wb') as f_out:
            # Write the IV to the output file (needed for decryption)
            f_out.write(iv)

            # Encrypt the file chunk by chunk
            while True:
                chunk = f_in.read(16)  # Read 16 bytes at a time
                if len(chunk) == 0:
                    break
                elif len(chunk) % 16 != 0:
                    # Add padding to the last block if needed
                    padder = padding.PKCS7(128).padder()
                    padded_data = padder.update(chunk) + padder.finalize()
                    chunk = padded_data
                encrypted_chunk = encryptor.update(chunk)
                f_out.write(encrypted_chunk)

            # Finalize the encryption (encryptor might have remaining data)
            final_chunk = encryptor.finalize()
            f_out.write(final_chunk)


def gzip_compress_file(input_file_path):
    # Extract the base filename without extension
    file_name, file_ext = os.path.splitext(input_file_path)
    
    # Output file path with .gz extension appended
    output_file_path = f'{file_name}.gz'
    
    with open(input_file_path, 'rb') as f_in:
        with gzip.open(output_file_path, 'wb') as f_out:
            f_out.writelines(f_in)
    
    return output_file_path

def gzip_compress_file_ps4(input_file_path):
    # Extract the base filename without extension
    file_name, file_ext = os.path.splitext(input_file_path)
    
    # Output file path with .gz extension appended
    output_file_path = f'{file_name}.bin'
    
    with open(input_file_path, 'rb') as f_in:
        with gzip.open(output_file_path, 'wb') as f_out:
            f_out.writelines(f_in)
    
    return output_file_path

def copy_folder(source_folder, destination_folder):
    """
    Copy the entire contents of source_folder to destination_folder.
    
    Args:
        source_folder (str): Path to the source folder to copy.
        destination_folder (str): Path to the destination folder.
    
    Returns:
        bool: True if copy operation is successful, False otherwise.
    """
    try:
        # Check if destination folder already exists
        if os.path.exists(destination_folder):
            print(f"Destination folder '{destination_folder}' already exists. Skipping copy.")
            return False
        
        # Copy the entire folder from source to destination
        shutil.copytree(source_folder, destination_folder)
        print(f"Folder '{source_folder}' successfully copied to '{destination_folder}'.")
        return True
    
    except shutil.Error as e:
        print(f"Error: {e}")
        return False
    
    except OSError as e:
        print(f"Error: {e}")
        return False

def export_data():
    selected_items = []
    for item_id in tree.get_children():
        if tree.set(item_id, "Select") == "☑":
            selected_items.append(item_id)

    game_platform = game_platform_var.get()

    game_region = game_region_var.get()

    max_concurrent = config["max_concurrent"]

    processed_ids = set()  # Track processed song IDs

    if game_platform == "PS4":
        output_dir = "out/Data/ORBIS/datatable"
        fumen_output_dir = "out/Data/ORBIS/fumen"
        fumen_hitwide_output_dir = "out/Data/ORBIS/fumen_hitwide"
        audio_output_dir = "out/Data/ORBIS/sound"
        musicinfo_filename = "musicinfo.json"
        max_entries = 400  # Maximum allowed entries for PS4
        platform_tag = "ps4"
    elif game_platform == "NS1":
        output_dir = "out/Data/NX/datatable"
        fumen_output_dir = "out/Data/NX/fumen/enso"
        fumen_hitwide_output_dir = "out/Data/NX/fumen_hitwide/enso"        
        fumen_hitnarrow_output_dir = "out/Data/NX/fumen_hitnarrow/enso"             
        audio_output_dir = "out/Data/NX/sound"
        musicinfo_filename = "musicinfo.json"
        max_entries = 600  # Maximum allowed entries for NS1
        platform_tag = "ns1"
    elif game_platform == "PTB":
        output_dir = "out/Data/Raw/ReadAssets"
        fumen_output_dir = "out/Data/Raw/fumen"
        audio_output_dir = "out/Data/Raw/sound/sound"
        musicinfo_filename = "musicinfo.json"
        songinfo_filename = "songinfo.json"
        max_entries = 200  # Maximum allowed entries for PTB
        platform_tag = "PTB"

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(fumen_output_dir, exist_ok=True)
    os.makedirs(audio_output_dir, exist_ok=True)

    selected_music_info = []
    selected_song_info = []    
    selected_wordlist = []
    current_unique_id = 0

    try:
        if len(selected_items) > max_entries:
            messagebox.showerror("Selection Limit Exceeded", f"Maximum {max_entries} entries can be selected for {game_platform}.")
            return

        # Load preview position data
        with open(previewpos_path, "r", encoding="utf-8") as previewpos_file:
            previewpos_data = json.load(previewpos_file)
        
        if custom_songs:
            with open(custom_previewpos_path, "r", encoding="utf-8") as custom_previewpos_file:
                custom_previewpos_data = json.load(custom_previewpos_file)            

        # Copy fumen folders for selected songs to output directory
        for item_id in selected_items:
            song_id = tree.item(item_id)["values"][1]
            fumen_folder_path = os.path.join(data_dir, "fumen", str(song_id))
            if os.path.exists(fumen_folder_path):
                shutil.copytree(fumen_folder_path, os.path.join(fumen_output_dir, f"{song_id}"))

            song_info = next((item for item in music_info["items"] if item["id"] == song_id), None)

        if custom_songs:
            for item_id in selected_items:

                song_id = tree.item(item_id)["values"][1]
                custom_fumen_folder_path = os.path.join(custom_data_dir, "fumen", str(song_id))
                if os.path.exists(custom_fumen_folder_path):
                    shutil.copytree(custom_fumen_folder_path, os.path.join(fumen_output_dir, f"{song_id}"))

                song_info = next((item for item in custom_music_info["items"] if item["id"] == song_id), None)

        for item_id in selected_items:
            song_id = tree.item(item_id)["values"][1]
            if custom_songs:
                combined_items = custom_music_info["items"] + music_info["items"]
            else:
                combined_items = music_info["items"]
    
            song_info = next((item for item in combined_items if item["id"] == song_id), None)

            if song_info:

                # Calculate song_order based on genreNo and current_unique_id
                song_order = (int(song_info["genreNo"]) * 1000) + current_unique_id
                
                if game_platform == "NS1":
                    ns1_song_info = {
                        "id": song_info["id"],
                        "uniqueId": current_unique_id,
                        "songFileName": song_info["songFileName"],
                        "order": song_order,
                        "genreNo": song_info["genreNo"],
		                "secretFlag":False,
                		"dlc":False,
                		"debug":False,
		                "recording":True,
                        "branchEasy": song_info["branchEasy"],
                        "branchNormal": song_info["branchNormal"],
                        "branchHard": song_info["branchHard"],
                        "branchMania": song_info["branchMania"],
                        "branchUra": song_info["branchUra"],
                        "starEasy": song_info["starEasy"],
                        "starNormal": song_info["starNormal"],
                        "starHard": song_info["starHard"],
                        "starMania": song_info["starMania"],
                        "starUra": song_info["starUra"],
                        "shinutiEasy": song_info["shinutiEasy"],
                        "shinutiNormal": song_info["shinutiNormal"],
                        "shinutiHard": song_info["shinutiHard"],
                        "shinutiMania": song_info["shinutiMania"],
                        "shinutiUra": song_info["shinutiUra"],
                        "shinutiEasyDuet": song_info["shinutiEasyDuet"],
                        "shinutiNormalDuet": song_info["shinutiNormalDuet"],
                        "shinutiHardDuet": song_info["shinutiHardDuet"],
                        "shinutiManiaDuet": song_info["shinutiManiaDuet"],
                        "shinutiUraDuet": song_info["shinutiUraDuet"],
                        "scoreEasy": song_info["scoreEasy"],
                        "scoreNormal": song_info["scoreNormal"],
                        "scoreHard": song_info["scoreHard"],
                        "scoreMania": song_info["scoreMania"],
                        "scoreUra": song_info["scoreUra"],
                        "alleviationEasy": False,
                        "alleviationNormal": False,
                        "alleviationHard": False,
                        "alleviationMania": False,
                        "alleviationUra": False,
                        "song_info1": 25721,
                        "song_info2": 39634,
                        "song_info3": 60504,
                        "song_info4": 79618,
                        "song_info5": 98750,
                        "song_info6": -1,
                        "song_info7": -1,
                        "song_info8": -1,
                        "song_info9": -1,
                        "song_info10": -1,
                        "aocID": song_info["id"],
                        "limitedID": -1,
                        "extraID": -1,
                        "tournamentRand": True,
                        "bgDon0": "",
                        "bgDancer0": "",
                        "bgFever0": "",
                        "chibi0": "",
                        "rendaEffect0": "",
                        "dancer0": "",
                        "feverEffect0": "",
                        "bgDon1": "",
                        "bgDancer1": "",
                        "bgFever1": "",
                        "chibi1": "",
                        "rendaEffect1": "",
                        "dancer1": "",
                        "feverEffect1": "",
                    }
                    selected_music_info.append(ns1_song_info)
                elif game_platform == "PS4":
                    ps4_song_info = {
                        "id": song_info["id"],
                        "uniqueId": current_unique_id,                       
                        "songFileName": song_info["songFileName"],
                        "order": song_order,
                        "genreNo": song_info["genreNo"],
		                "secretFlag":False,
	                	"dlc":False,
	                	"entitlementKey":"",
	                	"secondKey":False,
	                	"entitlementKey2":"",
	                	"debug":False,
                        "branchEasy": song_info["branchEasy"],
                        "branchNormal": song_info["branchNormal"],
                        "branchHard": song_info["branchHard"],
                        "branchMania": song_info["branchMania"],
                        "branchUra": song_info["branchUra"],
                        "starEasy": song_info["starEasy"],
                        "starNormal": song_info["starNormal"],
                        "starHard": song_info["starHard"],
                        "starMania": song_info["starMania"],
                        "starUra": song_info["starUra"],
                        "shinutiEasy": song_info["shinutiEasy"],
                        "shinutiNormal": song_info["shinutiNormal"],
                        "shinutiHard": song_info["shinutiHard"],
                        "shinutiMania": song_info["shinutiMania"],
                        "shinutiUra": song_info["shinutiUra"],
                        "shinutiEasyDuet": song_info["shinutiEasyDuet"],
                        "shinutiNormalDuet": song_info["shinutiNormalDuet"],
                        "shinutiHardDuet": song_info["shinutiHardDuet"],
                        "shinutiManiaDuet": song_info["shinutiManiaDuet"],
                        "shinutiUraDuet": song_info["shinutiUraDuet"],
                        "scoreEasy": song_info["scoreEasy"],
                        "scoreNormal": song_info["scoreNormal"],
                        "scoreHard": song_info["scoreHard"],
                        "scoreMania": song_info["scoreMania"],
                        "scoreUra": song_info["scoreUra"],
		                "secret":False,
	                	"songFileNameForSelect": song_info["songFileName"],
	                	"bgSolo0":"",
	                	"bgDuet0":"",
	                	"chibi0":"",
	                	"rendaEffect0":"",
	                	"dancer0":"",
	                	"feverEffect0":"",
	                	"bgSolo1":"",
	                	"bgDuet1":"",
                        "chibi1":"",
                        "rendaEffect1":"",
	                	"dancer1":"",
	                	"feverEffect1":""
                    }
                    selected_music_info.append(ps4_song_info)
                elif game_platform == "PTB":
                    ptb_song_info = {
                        "uniqueId": current_unique_id,                       
                        "id": song_info["id"],
                        "songFileName": song_info["songFileName"],
                        "order": song_order,
                        "genreNo": song_info["genreNo"],
		                "isLock":False,
	                	"isNew":False,
	                	"debug":False,
	                	"temp":False,
	                	"temp2":False,
                        "branchEasy": song_info["branchEasy"],
                        "branchNormal": song_info["branchNormal"],
                        "branchHard": song_info["branchHard"],
                        "branchMania": song_info["branchMania"],
                        "branchUra": song_info["branchUra"],
                        "starEasy": song_info["starEasy"],
                        "starNormal": song_info["starNormal"],
                        "starHard": song_info["starHard"],
                        "starMania": song_info["starMania"],
                        "starUra": song_info["starUra"],
                        "shinutiEasy": song_info["shinutiEasy"],
                        "shinutiNormal": song_info["shinutiNormal"],
                        "shinutiHard": song_info["shinutiHard"],
                        "shinutiMania": song_info["shinutiMania"],
                        "shinutiUra": song_info["shinutiUra"],
                        "shinutiEasyDuet": song_info["shinutiEasyDuet"],
                        "shinutiNormalDuet": song_info["shinutiNormalDuet"],
                        "shinutiHardDuet": song_info["shinutiHardDuet"],
                        "shinutiManiaDuet": song_info["shinutiManiaDuet"],
                        "shinutiUraDuet": song_info["shinutiUraDuet"],
                        "scoreEasy": song_info["scoreEasy"],
                        "scoreNormal": song_info["scoreNormal"],
                        "scoreHard": song_info["scoreHard"],
                        "scoreMania": song_info["scoreMania"],
                        "scoreUra": song_info["scoreUra"],
                    }
                    selected_music_info.append(ptb_song_info)

                    # Find previewPos from previewpos.json based on song_id
                    preview_pos = None
                    for item in previewpos_data:
                        if item["id"] == song_info["id"]:
                            preview_pos = item["previewPos"]
                            break

                    ptb_extra_song_info = {
                        "uniqueId": current_unique_id,                       
                        "id": song_info["id"],
                        "previewPos": preview_pos if preview_pos is not None else 0,  # Use 0 if previewPos not found
		                "fumenOffsetPos":0
                    }
                    selected_song_info.append(ptb_extra_song_info)
                current_unique_id += 1

                # Find the wordlist items corresponding to song variations
                word_keys = [f"song_{song_id}", f"song_sub_{song_id}", f"song_detail_{song_id}"]
                
                def find_word_info(key, word_lists):
                    for word_list in word_lists:
                        word_info = next((item for item in word_list["items"] if item["key"] == key), None)
                        if word_info:
                            return word_info
                    return None
                
                word_lists = [word_list]
                if custom_songs:
                    word_lists.append(custom_word_list)
                
                for key in word_keys:
                    word_info = find_word_info(key, word_lists)
                    if word_info:
                        selected_wordlist.append(word_info)

                if game_platform == "PS4":
                    # Find the corresponding preview position for the current song_id
                    preview_pos = next((item["previewPos"] for item in previewpos_data if item["id"] == song_id), None)
                    if custom_songs:
                        custom_preview_pos = next((item["previewPos"] for item in custom_previewpos_data if item["id"] == song_id), None)

                    def convert_song(song_id, custom_songs):
                        preview_pos = get_preview_pos(song_id)
                        if custom_songs and custom_preview_pos is not None:
                            song_filename = os.path.join(custom_data_dir, "sound", f"song_{song_id}.mp3")
                        else:
                            song_filename = os.path.join(data_dir, "sound", f"song_{song_id}.mp3")

                        output_file = os.path.join(audio_output_dir, f"song_{song_id}.nus3bank")
                        #command = [
                        #    "python",
                        #    "nus3bank.py",
                        #    song_filename,
                        #    "at9",
                        #    platform_tag,
                        #    str(preview_pos),  # Convert preview_pos to string
                        #    song_id
                        #]
                        #subprocess.run(command)
                        convert_audio_to_nus3bank(song_filename, "at9", platform_tag, str(preview_pos), song_id)
                    
                        if os.path.exists(f"song_{song_id}.nus3bank"):
                            shutil.move(f"song_{song_id}.nus3bank", output_file)
                            print(f"Created {output_file} successfully.")
                        else:
                            print(f"Conversion failed for song_{song_id}.")
                        if os.path.exists(f"song_{song_id}.mp3.at9"):
                            os.remove(f"song_{song_id}.mp3.at9")
                            print(f"Deleted song_{song_id}.mp3.at9")

                    # Check if preview_pos or custom_preview_pos is not None and run conversion
                    if preview_pos is not None or (custom_songs and custom_preview_pos is not None):
                        convert_song(song_id, custom_songs)                    
                        
                elif game_platform == "PTB":
                    # Find the corresponding preview position for the current song_id
                    preview_pos = next((item["previewPos"] for item in previewpos_data if item["id"] == song_id), None)
                    if custom_songs:
                        custom_preview_pos = next((item["previewPos"] for item in custom_previewpos_data if item["id"] == song_id), None)

                    def convert_song(song_id, custom_songs):
                        preview_pos = get_preview_pos(song_id)
                        if custom_songs and custom_preview_pos is not None:
                            song_filename = os.path.join(custom_data_dir, "sound", f"song_{song_id}.mp3")
                        else:
                            song_filename = os.path.join(data_dir, "sound", f"song_{song_id}.mp3")                        
                        output_file = os.path.join(audio_output_dir, f"song_{song_id}.bin")
                        create_and_encrypt_acb(song_filename, song_id)
                        shutil.move(f"song_{song_id}.bin", output_file)     

                    # Check if preview_pos or custom_preview_pos is not None and run conversion
                    if preview_pos is not None or (custom_songs and custom_preview_pos is not None):
                        convert_song(song_id, custom_songs)                                                          

                elif game_platform == "NS1":
                    # Find the corresponding preview position for the current song_id
                    preview_pos = next((item["previewPos"] for item in previewpos_data if item["id"] == song_id), None)
                    if custom_songs:
                        custom_preview_pos = next((item["previewPos"] for item in custom_previewpos_data if item["id"] == song_id), None)

                    def convert_song(song_id, custom_songs):
                        preview_pos = get_preview_pos(song_id)
                        if custom_songs and custom_preview_pos is not None:
                            song_filename = os.path.join(custom_data_dir, "sound", f"song_{song_id}.mp3")
                        else:
                            song_filename = os.path.join(data_dir, "sound", f"song_{song_id}.mp3")

                        output_file = os.path.join(audio_output_dir, f"song_{song_id}.nus3bank")
                        #command = [
                        #    "python",
                        #    "nus3bank.py",
                        #    song_filename,
                        #    "idsp",
                        #    platform_tag,
                        #    str(preview_pos),  # Convert preview_pos to string
                        #    song_id
                        #]
                        #subprocess.run(command)
                        convert_audio_to_nus3bank(song_filename, "idsp", platform_tag, str(preview_pos), song_id)
                        if os.path.exists(f"song_{song_id}.nus3bank"):
                            shutil.move(f"song_{song_id}.nus3bank", output_file)
                            print(f"Created {output_file} successfully.")
                        else:
                            print(f"Conversion failed for song_{song_id}.")
                        if os.path.exists(f"song_{song_id}.mp3.idsp"):
                            os.remove(f"song_{song_id}.mp3.idsp")
                            print(f"Deleted song_{song_id}.mp3.idsp")

                    # Check if preview_pos or custom_preview_pos is not None and run conversion
                    if preview_pos is not None or (custom_songs and custom_preview_pos is not None):
                        convert_song(song_id, custom_songs)

        # Export selected musicinfo and wordlist
        if game_platform == "PTB":

            selected_musicinfo_path = os.path.join(output_dir, musicinfo_filename)
            selected_wordlist_path = os.path.join(output_dir, "wordlist.json")
            selected_songinfo_path = os.path.join(output_dir, songinfo_filename) 

            with open(selected_songinfo_path, "w", encoding="utf-8") as out_musicinfo_file:
                json.dump({"items": selected_song_info}, out_musicinfo_file, ensure_ascii=False, indent=4)

            with open(selected_musicinfo_path, "w", encoding="utf-8") as out_musicinfo_file:
                json.dump({"items": selected_music_info}, out_musicinfo_file, ensure_ascii=False, indent=4)

            with open(selected_wordlist_path, "w", encoding="utf-8") as out_wordlist_file:
                json.dump({"items": selected_wordlist}, out_wordlist_file, ensure_ascii=False, indent=4)

            merge_ptb('data\\_console\\Raw\\ReadAssets\\wordlist.json', 'out\\Data\\Raw\\ReadAssets\\wordlist.json', 'out\\Data\\Raw\\ReadAssets\\wordlist.json')

            #Compress each ReadAsset file
            gzip_compress_file(selected_musicinfo_path)
            gzip_compress_file(selected_wordlist_path)
            gzip_compress_file(selected_songinfo_path)

            #Compress each Remove the json files
            os.remove(selected_musicinfo_path)
            os.remove(selected_wordlist_path)
            os.remove(selected_songinfo_path)

            #Compressed File definitions
            compressed_musicinfo_path = os.path.join(output_dir, "musicinfo.gz")
            compressed_wordlist_path = os.path.join(output_dir, "wordlist.gz")
            compressed_songinfo_path = os.path.join(output_dir, "songinfo.gz")             

            # Final Output definitions
            final_musicinfo = os.path.join(output_dir, "musicinfo.bin")
            final_wordlist = os.path.join(output_dir, "wordlist.bin")
            final_songinfo = os.path.join(output_dir, "songinfo.bin")    

            # Encrypt the final files
            encrypt_file_ptb(compressed_musicinfo_path, final_musicinfo)
            encrypt_file_ptb(compressed_wordlist_path, final_wordlist)
            encrypt_file_ptb(compressed_songinfo_path, final_songinfo)   

            # Remove compressed .gz files
            os.remove(compressed_musicinfo_path)
            os.remove(compressed_wordlist_path)
            os.remove(compressed_songinfo_path)                                

        elif game_platform == "PS4":

            selected_musicinfo_path = os.path.join(output_dir, musicinfo_filename)
            selected_wordlist_path = os.path.join(output_dir, "wordlist.json")

            with open(selected_musicinfo_path, "w", encoding="utf-8") as out_musicinfo_file:
                json.dump({"items": selected_music_info}, out_musicinfo_file, ensure_ascii=False, indent=4)

            with open(selected_wordlist_path, "w", encoding="utf-8") as out_wordlist_file:
                json.dump({"items": selected_wordlist}, out_wordlist_file, ensure_ascii=False, indent=4)            

            if game_region == "JPN/ASIA":
                merge_ps4_jp('data\\_console\\ORBIS\\datatablejp\\wordlist.json', 'out\\Data\\ORBIS\\datatable\\wordlist.json', 'out\\Data\\ORBIS\\datatable\\wordlist.json')
            elif game_region == "EU/USA":
                merge_ps4_int('data\\_console\\ORBIS\\datatableint\\wordlist.json', 'out\\Data\\ORBIS\\datatable\\wordlist.json', 'out\\Data\\ORBIS\\datatable\\wordlist.json')

            #Compress each datatable file
            gzip_compress_file_ps4(selected_musicinfo_path)
            gzip_compress_file_ps4(selected_wordlist_path)

            #Remove .json files
            os.remove(selected_musicinfo_path)
            os.remove(selected_wordlist_path)

            copy_folder(fumen_output_dir,fumen_hitwide_output_dir)

        elif game_platform == "NS1":
            
            selected_musicinfo_path = os.path.join(output_dir, musicinfo_filename)
            selected_wordlist_path = os.path.join(output_dir, "wordlist.json")

            with open(selected_musicinfo_path, "w", encoding="utf-8") as out_musicinfo_file:
                json.dump({"items": selected_music_info}, out_musicinfo_file, ensure_ascii=False, indent=4)

            with open(selected_wordlist_path, "w", encoding="utf-8") as out_wordlist_file:
                json.dump({"items": selected_wordlist}, out_wordlist_file, ensure_ascii=False, indent=4)            

            if game_region == "JPN/ASIA":
                merge_ns1_jp('data\\_console\\NX\\datatable\\wordlist.json', 'out\\Data\\NX\\datatable\\wordlist.json', 'out\\Data\\NX\\datatable\\wordlist.json')
            elif game_region == "EU/USA":
                merge_ns1_int('data\\_console\\NX\\datatable\\wordlist.json', 'out\\Data\\NX\\datatable\\wordlist.json', 'out\\Data\\NX\\datatable\\wordlist.json')


            #Compress each datatable file
            gzip_compress_file(selected_musicinfo_path)
            gzip_compress_file(selected_wordlist_path)

            #Compress each Remove the json files
            os.remove(selected_musicinfo_path)
            os.remove(selected_wordlist_path)

            #Compressed File definitions
            compressed_musicinfo_path = os.path.join(output_dir, "musicinfo.gz")
            compressed_wordlist_path = os.path.join(output_dir, "wordlist.gz")        

            # Final Output definitions
            final_musicinfo = os.path.join(output_dir, "musicinfo.bin")
            final_wordlist = os.path.join(output_dir, "wordlist.bin")

            # Encrypt the final files
            encrypt_file_ns1(compressed_musicinfo_path, final_musicinfo)
            encrypt_file_ns1(compressed_wordlist_path, final_wordlist)

            # Remove compressed .gz files
            os.remove(compressed_musicinfo_path)
            os.remove(compressed_wordlist_path)

            copy_folder(fumen_output_dir,fumen_hitwide_output_dir)
            copy_folder(fumen_output_dir,fumen_hitnarrow_output_dir)

        messagebox.showinfo("Export Completed", "Selected songs exported successfully!")

    except Exception as e:
        messagebox.showerror("Export Error", f"An error occurred during export: {str(e)}")

#Button shenanigans, because the order they appear on the gui, is determined by the literal order they are in the code???

# Top Side

if lang == "jp":
    preview_button = ttk.Button(main_frame, text="オーディオ・プレビュー", command=preview_selected)
else:
    preview_button = ttk.Button(main_frame, text="Preview", command=preview_selected)
preview_button.pack(side="top", padx=20, pady=10)

# Create sorting options
if lang == "jp":
    sort_options = ["ID", "Song Name", "Genre"]
    sort_label = tk.Label(main_frame, text="ソートフィルター：")
else:
    sort_options = ["ID", "Song Name", "Genre"]
    sort_label = tk.Label(main_frame, text="Sort by:")
sort_label.pack(side="top", padx=20, pady=5)

sort_var = tk.StringVar(main_frame)
sort_var.set("ID")
sort_menu = ttk.Combobox(main_frame, textvariable=sort_var, values=sort_options)
sort_menu.bind("<<ComboboxSelected>>", lambda _: sort_tree(sort_var.get()))
sort_menu.pack(side="top", padx=20, pady=0)

search_entry.pack(side="top", padx=20, pady=10, fill="x") # search bar, currently broken

# Bottom Side
if lang == "jp":
    export_button = ttk.Button(main_frame, text="エクスポート", command=export_data)
else:
    export_button = ttk.Button(main_frame, text="Export", command=export_data)    
export_button.pack(side="bottom", padx=20, pady=10)

# Create Selection Count Label
selection_count_label = ttk.Label(main_frame, text="0/???")
selection_count_label.pack(side="bottom", padx=20, pady=10)

# Game platform selection
game_platform_var = tk.StringVar(main_frame)
game_platform_var.set("PS4")
game_platform_choices = ["PS4", "NS1", "PTB"]
game_platform_menu = ttk.Combobox(main_frame, textvariable=game_platform_var, values=game_platform_choices)
game_platform_menu.pack(side="bottom", padx=20, pady=0)

# Create Label for Platform selection
if lang == "jp":
    platform_label = tk.Label(main_frame, text="ゲーム機：")
else:
    platform_label = tk.Label(main_frame, text="Platform")
platform_label.pack(side="bottom", padx=20, pady=5)

# Game region selection, needed for wordlist export
game_region_var = tk.StringVar(main_frame)
game_region_var.set("JPN/ASIA")
game_region_choices = ["JPN/ASIA", "EU/USA"]
game_region_menu = ttk.Combobox(main_frame, textvariable=game_region_var, values=game_region_choices)
game_region_menu.pack(side="bottom", padx=20, pady=10)

# Create Label for Region selection
if lang == "jp":
    game_region_label = tk.Label(main_frame, text="ゲーム地域：")
else:
    game_region_label = tk.Label(main_frame, text="Game Region:")
game_region_label.pack(side="bottom", padx=20, pady=0)


# Doesn't function?
# Update selection count when tree selection changes
#tree.bind("<<TreeviewSelect>>", lambda event: update_selection_count())

window.mainloop()
