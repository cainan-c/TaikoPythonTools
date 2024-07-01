import concurrent.futures
import functools
import glob
import concurrent.futures 
import gzip
import json
import numpy as np
import os
import random
import re
import shutil
import subprocess
import struct
import tempfile
import tkinter as tk
import sv_ttk
import xml.etree.ElementTree as ET
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from PIL import Image, ImageDraw, ImageFont
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
    platform = game_platform_var.get()

    for item_id in selected_items:
        values = list(tree.item(item_id, "values"))
        song_id = values[1]  # Ensure this points to the correct column for song ID

        # Retrieve the song data to check the starUra value
        song = next((song for song in music_info["items"] if str(song["id"]) == song_id), None)
        if custom_songs and not song:
            song = next((song for song in custom_music_info["items"] if str(song["id"]) == song_id), None)

        star_ura = song.get("starUra", 0) if song else 0
        increment = 1

        if platform == "WIIU3" and star_ura > 0:
            increment = 2

        if values[0] == "☐":
            values[0] = "☑"
            if song_id not in selected_song_ids:
                selected_song_ids.append(song_id)
                selection_count.set(selection_count.get() + increment)
        else:
            values[0] = "☐"
            if song_id in selected_song_ids:
                selected_song_ids.remove(song_id)
                selection_count.set(selection_count.get() - increment)

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
    elif platform == "WIIU3":
        max_entries = 90 # this is due to us using RGBA for textures. High quality = less textures can be added.
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

def clear_selection():
    # Get all items in the treeview
    all_items = tree.get_children()

    for item_id in all_items:
        values = list(tree.item(item_id, "values"))
        song_id = values[1]  # Ensure this points to the correct column for song ID

        if values[0] == "☑":
            values[0] = "☐"
            tree.item(item_id, values=values)

    # Clear the selected song IDs and reset the selection count
    selected_song_ids.clear()
    selection_count.set(0)

    # Update the selection count display
    update_selection_count()

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

#wiiu3 texture gen
# Define a dictionary for vertical forms of certain punctuation marks
# Define a dictionary for vertical forms of certain punctuation marks
rotated_chars = {
    '「': '﹁', '」': '﹂',
    '『': '﹃', '』': '﹄',
    '（': '︵', '）': '︶',
    '［': '﹇', '］': '﹈',
    '〝': '﹁', '〟': '﹂',
    '｛': '︷', '｝': '︸',
    '｟': '︹', '｠': '︺',
    '＜': '︿', '＞': '﹀',
    '《': '︽', '》': '︾',
    '〈': '︿', '〉': '﹀',
    '【': '︻', '】': '︼',
    '〔': '︹', '〕': '︺',
    '「': '﹁', '」': '﹂',
    '『': '﹃', '』': '﹄',
    '（': '︵', '）': '︶',
    '［': '﹇', '］': '﹈',
    '｛': '︷', '｝': '︸',
    '〈': '︿', '〉': '﹀',
    '《': '︽', '》': '︾',
    '【': '︻', '】': '︼',
    '〔': '︹', '〕': '︺',
    '～': '｜', '～': '｜',
    '(': '︵', ')': '︶',
}

rotated_letters = {
    'ー': '｜', '-': '｜'
}

full_width_chars = {
    'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E', 'Ｆ': 'F', 'Ｇ': 'G', 'Ｈ': 'H', 'Ｉ': 'I',
    'Ｊ': 'J', 'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N', 'Ｏ': 'O', 'Ｐ': 'P', 'Ｑ': 'Q', 'Ｒ': 'R',
    'Ｓ': 'S', 'Ｔ': 'T', 'Ｕ': 'U', 'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X', 'Ｙ': 'Y', 'Ｚ': 'Z',
    'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e', 'ｆ': 'f', 'ｇ': 'g', 'ｈ': 'h', 'ｉ': 'i',
    'ｊ': 'j', 'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n', 'ｏ': 'o', 'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r',
    'ｓ': 's', 'ｔ': 't', 'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x', 'ｙ': 'y', 'ｚ': 'z'
}

def convert_full_width(text):
    converted_text = ''
    for char in text:
        converted_text += full_width_chars.get(char, char)
    return converted_text


def get_text_bbox(draw, text, font):
    return draw.textbbox((0, 0), text, font=font)

def generate_image(draw, text, font, rotated_font, size, position, alignment, stroke_width, stroke_fill, fill, vertical=False, vertical_small=False):
    width, height = size

    # Calculate initial text dimensions
    text_bbox = get_text_bbox(draw, text, font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    if vertical or vertical_small:
        text_height = 0
        max_char_width = 0
        for char in text:
            char_font = rotated_font if char in rotated_chars else font
            char = rotated_chars.get(char, char)
            char = rotated_letters.get(char, char)
            text_bbox = get_text_bbox(draw, char, char_font)
            text_height += text_bbox[3] - text_bbox[1]
            char_width = text_bbox[2] - text_bbox[0]
            if char_width > max_char_width:
                max_char_width = char_width

        text_height = max(0, text_height - 1)  # Remove the last extra space
        text_position = (position[0] - max_char_width / 2, (height - text_height) / 2)
    else:
        text_bbox = get_text_bbox(draw, text, font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        if alignment == 'center':
            text_position = ((width - text_width) / 2, position[1])
        elif alignment == 'right':
            text_position = (width - text_width, position[1])
        else:
            text_position = position

    if vertical:
        y_offset = 5
        for char in text:
            char_font = rotated_font if char in rotated_chars else font
            char = rotated_chars.get(char, char)
            char = rotated_letters.get(char, char)
            text_bbox = get_text_bbox(draw, char, char_font)
            char_height = (text_bbox[3] + text_bbox[1])
            char_width = text_bbox[2] - text_bbox[0]
            draw.text((text_position[0] - char_width / 2, y_offset), char, font=char_font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
            y_offset += char_height
    elif vertical_small:
        y_offset = 5
        for char in text:
            char_font = rotated_font if char in rotated_chars else font
            char = rotated_chars.get(char, char)
            char = rotated_letters.get(char, char)
            text_bbox = get_text_bbox(draw, char, char_font)
            char_height = (text_bbox[3] + text_bbox[1])
            char_width = text_bbox[2] - text_bbox[0]
            draw.text((text_position[0] - char_width / 2, y_offset), char, font=char_font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
            y_offset += char_height            
    else:
        draw.text(text_position, text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)

def create_images(data, id, genreNo, font_path, rotated_font_path, current_unique_id, append_ura=False):
    font_size_extra_large = 46.06875 
    font_size_large = 40.60875 
    font_size_medium = 27.3
    font_size_small = 21.84 

    img_3_5_height = 400
    formatted_id = f"{current_unique_id:04d}"
    texture_output_dir = f"out/content/{formatted_id}/texture"

    folder_name = os.path.join(texture_output_dir, id)
    os.makedirs(folder_name, exist_ok=True)

    # Define genre colors
    genre_colors = [
        (0, 78, 88),    # pop
        (159, 61, 2),   # anime
        (90, 98, 129),  # vocaloid
        (55, 74, 0),    # variety        
        (0, 0, 0),      # unused (kids)
        (115, 77, 0),   # classic
        (82, 32, 115),  # game music
        (156, 36, 8),   # namco original
    ]

    genre_color = genre_colors[genreNo]

    # Initialize text variables
    japanese_text = ""
    japanese_sub_text = ""

    # Find the relevant texts
    for item in data['items']:
        if item['key'] == f'song_{id}':
            japanese_text = item['japaneseText']
        if item['key'] == f'song_sub_{id}':
            japanese_sub_text = item['japaneseText']

    # Convert full-width English characters to normal ASCII characters
    japanese_text = convert_full_width(japanese_text)
    japanese_sub_text = convert_full_width(japanese_sub_text) if japanese_sub_text else ''

    # Append "─" character if -ura argument is provided
    if append_ura:
        japanese_text += " ─"

    japanese_text += " "

    if japanese_sub_text.startswith("--"):
        japanese_sub_text = japanese_sub_text[2:]

    # Check if texts were found
    if not japanese_text:
        print(f"Error: No Japanese text found for song_{id}")
        return
    if not japanese_sub_text:
        print(f"Warning: No Japanese sub text found for song_sub_{id}")

    font_extra_large = ImageFont.truetype(font_path, int(font_size_extra_large))
    font_large = ImageFont.truetype(font_path, int(font_size_large))
    font_medium = ImageFont.truetype(font_path, int(font_size_medium))
    font_small = ImageFont.truetype(font_path, int(font_size_small))
    rotated_font = ImageFont.truetype(rotated_font_path, int(font_size_medium))

    # Image 0.png
    img0_width = 720

    img0 = Image.new('RGBA', (img0_width, 64), color=(0, 0, 0, 0))
    draw0 = ImageDraw.Draw(img0)

    temp_img0 = Image.new('RGBA', (2880, 64), (0, 0, 0, 0))  # Temporary image with 2880px width
    temp_draw0 = ImageDraw.Draw(temp_img0)

    # Generate the image with the Japanese text
    generate_image(temp_draw0, japanese_text, font_large, rotated_font, (2880, 64), (0, 10), 'right', 5, 'black', 'white')

    # Calculate the bounding box of the entire text
    text_bbox = get_text_bbox(temp_draw0, japanese_text, font_large)
    text_width = (text_bbox[2] - text_bbox[0]) + 5

    # Resize the image if it exceeds the specified height
    if text_width > img0_width:
        cropped_img = temp_img0.crop((2880 - text_width, 0, 2880, 64))

        scaled_img = cropped_img.resize((img0_width, 64), Image.Resampling.LANCZOS)

        final_img0 = Image.new('RGBA', (img0_width, 64), (0, 0, 0, 0))
        final_img0.paste(scaled_img)
    else:
    # Crop the temporary image to the actual width of the text
        cropped_img = temp_img0.crop((2880 - text_width, 0, 2880, 64))
        final_img0 = Image.new('RGBA', (img0_width, 64), (0, 0, 0, 0))
        final_img0.paste(cropped_img, (img0_width - text_width, 0))

    # Create a new image with the specified width and right-align the text
    #final_img0 = Image.new('RGBA', (img0_width, 64), (0, 0, 0, 0))
    #final_img0.paste(cropped_img, (img0_width - text_width, 0))

    # Save the final image
    final_img0.save(os.path.join(folder_name, '0.png'))

    # Image 1.png
    img1 = Image.new('RGBA', (720, 104), color=(0, 0, 0, 0))
    draw1 = ImageDraw.Draw(img1)
    generate_image(draw1, japanese_text, font_extra_large, rotated_font, (720, 104), (0, 13), 'center', 5, 'black', 'white')
    generate_image(draw1, japanese_sub_text, font_medium, rotated_font, (720, 104), (0, 68), 'center', 4, 'black', 'white')
    img1.save(os.path.join(folder_name, '1.png'))

    # Image 2.png
    img2 = Image.new('RGBA', (720, 64), color=(0, 0, 0, 0))
    draw2 = ImageDraw.Draw(img2)
    generate_image(draw2, japanese_text, font_large, rotated_font, (720, 64), (0, 4), 'center', 5, 'black', 'white')
    img2.save(os.path.join(folder_name, '2.png'))

    # Image 3.png    

    img3_height = 400

    img3 = Image.new('RGBA', (96, 400), color=(0, 0, 0, 0))
    img3_1 = Image.new('RGBA', (96, 400), color=(0, 0, 0, 0))
    img3_2 = Image.new('RGBA', (96, 400), color=(0, 0, 0, 0))
    draw3 = ImageDraw.Draw(img3)

    temp_img3 = Image.new('RGBA', (96, 3000), (0, 0, 0, 0))  # Temporary image with 1000px height
    temp_draw3 = ImageDraw.Draw(temp_img3)

    temp_sub_img3 = Image.new('RGBA', (96, 3000), (0, 0, 0, 0))  # Temporary image with 1000px height
    temp_sub_draw3 = ImageDraw.Draw(temp_sub_img3)

    generate_image(temp_draw3, japanese_text, font_large, rotated_font, (96, 3000), (89, 0), 'center', 5, 'black', 'white', vertical=True)

    # Crop the temporary image to the actual height of the text
    y_offset = 0
    for char in japanese_text:
        char_font = rotated_font if char in rotated_chars else font_large
        char = rotated_chars.get(char, char)
        char = rotated_letters.get(char, char)
        text_bbox = get_text_bbox(temp_draw3, char, char_font)
        char_height = (text_bbox[3] + text_bbox[1])
        y_offset += char_height

    # Crop the temporary image to the actual height of the text
    temp_img3 = temp_img3.crop((0, 0, 96, y_offset))

    # Resize the image if it exceeds the specified height
    if y_offset > img3_height:
        img3_1 = temp_img3.resize((96, img3_height), Image.Resampling.LANCZOS)
    else:
        img3_1 = temp_img3.crop((0, 0, 96, img3_height))

    generate_image(temp_sub_draw3, japanese_sub_text, font_medium, rotated_font, (96, 3000), (32, 156), 'center', 4, 'black', 'white', vertical_small=True)

    # Crop the temporary image to the actual height of the text
    y_offset = 0
    for char in japanese_sub_text:
        char_font = rotated_font if char in rotated_chars else font_medium
        char = rotated_chars.get(char, char)
        char = rotated_letters.get(char, char)
        text_bbox = get_text_bbox(temp_sub_draw3, char, char_font)
        char_height = round((text_bbox[3] + text_bbox[1]) * 1.1)
        y_offset += char_height

    # Crop the temporary image to the actual height of the text
    temp_sub_img3 = temp_sub_img3.crop((0, 0, 96, y_offset))

    # Resize the image if it exceeds the specified height
    if y_offset > img3_height:
        img3_2 = temp_sub_img3.resize((96, img3_height), Image.Resampling.LANCZOS)
    else:
        img3_2 = temp_sub_img3.crop((0, 0, 96, img3_height))

    img3.paste(img3_1, (0, 0))
    img3.paste(img3_2, (0, 0), img3_2) 
    img3.save(os.path.join(folder_name, '3.png'))

    # Image 4.png
    img4_height = 400

    img4 = Image.new('RGBA', (56, 400), color=(0, 0, 0, 0))
    draw4 = ImageDraw.Draw(img4)

    temp_img4 = Image.new('RGBA', (56, 3000), (0, 0, 0, 0))  # Temporary image with 3000px height
    temp_draw4 = ImageDraw.Draw(temp_img4)

    generate_image(temp_draw4, japanese_text, font_large, rotated_font, (56, 400), (48, 0), 'center', 5, genre_color, 'white', vertical=True)

    # Crop the temporary image to the actual height of the text
    y_offset = 0
    for char in japanese_text:
        char_font = rotated_font if char in rotated_chars else font_large
        char = rotated_chars.get(char, char)
        char = rotated_letters.get(char, char)
        text_bbox = get_text_bbox(temp_draw4, char, char_font)
        char_height = (text_bbox[3] + text_bbox[1])
        y_offset += char_height

    # Crop the temporary image to the actual height of the text
    temp_img4 = temp_img4.crop((0, 0, 56, y_offset))

    # Resize the image if it exceeds the specified height
    if y_offset > img4_height:
        img4 = temp_img4.resize((56, img4_height), Image.Resampling.LANCZOS)
    else:
        img4 = temp_img4.crop((0, 0, 56, img4_height))

    img4.save(os.path.join(folder_name, '4.png'))

    # Image 5.png
    img5_height = 400

    img5 = Image.new('RGBA', (56, 400), color=(0, 0, 0, 0))
    draw5 = ImageDraw.Draw(img5)

    temp_img5 = Image.new('RGBA', (56, 3000), (0, 0, 0, 0))  # Temporary image with 1000px height
    temp_draw5 = ImageDraw.Draw(temp_img5)

    generate_image(temp_draw5, japanese_text, font_large, rotated_font, (56, 400), (48, 0), 'center', 5, 'black', 'white', vertical=True)

    # Crop the temporary image to the actual height of the text
    y_offset = 0
    for char in japanese_text:
        char_font = rotated_font if char in rotated_chars else font_large
        char = rotated_chars.get(char, char)
        char = rotated_letters.get(char, char)
        text_bbox = get_text_bbox(temp_draw5, char, char_font)
        char_height = (text_bbox[3] + text_bbox[1])
        y_offset += char_height

    # Crop the temporary image to the actual height of the text
    temp_img5 = temp_img5.crop((0, 0, 56, y_offset))

    # Resize the image if it exceeds the specified height
    if y_offset > img5_height:
        img5 = temp_img5.resize((56, img5_height), Image.Resampling.LANCZOS)
    else:
        img5 = temp_img5.crop((0, 0, 56, img5_height))

    img5.save(os.path.join(folder_name, '5.png'))

def generate_wiiu3_texture(id, genreNo, current_unique_id, append_ura, custom_songs):
    # Load your JSON data from a file
    if custom_songs == True:
        with open(rf'{custom_wordlist_path}', encoding='utf-8') as f:
            data = json.load(f)
    else:
        with open(rf'{wordlist_path}', encoding='utf-8') as f:
            data = json.load(f)

    font_path = 'data/_resource/font/DFPKanTeiRyu-XB.ttf'
    rotated_font_path = 'data/_resource/font/KozGoPr6NRegular.otf'
    create_images(data, id, genreNo, font_path, rotated_font_path, current_unique_id, append_ura)

class TextureSurface:
    def __init__(self):
        self.mipmaps = []

class NutTexture:
    def __init__(self, width, height, pixel_format, pixel_type):
        self.surfaces = [TextureSurface()]
        self.Width = width
        self.Height = height
        self.pixelInternalFormat = pixel_format
        self.pixelFormat = pixel_type

    def add_mipmap(self, mipmap_data):
        self.surfaces[0].mipmaps.append(mipmap_data)

    @property
    def MipMapsPerSurface(self):
        return len(self.surfaces[0].mipmaps)

    def getNutFormat(self):
        if self.pixelInternalFormat == 'RGBA':
            return 14
        elif self.pixelInternalFormat == 'CompressedRgbaS3tcDxt5Ext':
            return 28  # Example format code for DXT5, adjust as necessary
        raise NotImplementedError("Only RGBA format is implemented")

class NUT:
    def __init__(self):
        self.textures = []

    def add_texture(self, texture):
        self.textures.append(texture)

    def save(self, filename):
        with open(filename, 'wb') as f:
            f.write(self.build())

    def build(self):
        data = bytearray()
        num_textures = len(self.textures)
        # File header
        header = struct.pack(">IHH", 0x4E545033, 0x0200, num_textures)
        data.extend(header)

        # Initial offset (0x18 bytes for the header, then 0x4 bytes per texture offset)
        texture_offset_base = 0x18 + (0x4 * num_textures)
        texture_headers_offset = texture_offset_base
        texture_data_offset = texture_headers_offset + (0x50 * num_textures)

        # Ensure texture data starts at the correct offset (0x42E0)
        texture_data_offset = max(texture_data_offset, 0x4000)

        # Offset table
        texture_offsets = []
        for texture in self.textures:
            texture_offsets.append(texture_data_offset)
            texture_data_offset += 0x50 + sum(len(mipmap) for mipmap in texture.surfaces[0].mipmaps)

        for offset in texture_offsets:
            data.extend(struct.pack(">I", offset))
        
        # Texture headers and mipmaps
        for texture, offset in zip(self.textures, texture_offsets):
            data.extend(self.build_texture_header(texture, offset))
        
        for texture in self.textures:
            for mipmap in texture.surfaces[0].mipmaps:
                data.extend(mipmap)

        return data

    def build_texture_header(self, texture, offset):
        mipmap_count = texture.MipMapsPerSurface
        size = texture.Width * texture.Height * 4  # Texture size
        header = struct.pack(">IIIIHHIIII",
                             size, texture.Width, texture.Height, 0, 0,
                             mipmap_count, texture.getNutFormat(),
                             texture.Width, texture.Height, 0)
        additional_data = b'\x65\x58\x74\x00\x00\x00\x00\x20\x00\x00\x00\x10\x00\x00\x00\x00' \
                          b'\x47\x49\x44\x58\x00\x00\x00\x10\x00\x00\x00\x05\x00\x00\x00\x00'
        return header + additional_data.ljust(0x50 - len(header), b'\x00')

    def modify_nut_file(self, file_path, output_path):
        # Set replacement bytes to 00

        with open(file_path, 'rb') as f:
            data = bytearray(f.read())
        
        # Replace bytes from 0x00 to 0x1F0
        #data[0x00:0x1EF] = replacement_bytes
        # Delete bytes from 0x42E0 to 0x42F3 (0x42E0 to 0x42F4 inclusive)
        del data[0x42E0:0x42F3]
        del data[0x0040:0x0044]
        data[0x1F0:0x1F0] = b'\x00\x00\x00\x00'
        data[0x008:0x010] = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        data[0x010:0x040] = b'\x00\x02\xd0P\x00\x00\x00\x00\x00\x02\xd0\x00\x00P\x00\x00\x00\x01\x00\x0e\x02\xd0\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\xe0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data[0x060:0x090] = b'\x00\x04\x92P\x00\x00\x00\x00\x00\x04\x92\x00\x00P\x00\x00\x00\x01\x00\x0e\x02\xd0\x00h\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xd1\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data[0x0B0:0x0E0] = b'\x00\x02\xd0P\x00\x00\x00\x00\x00\x02\xd0\x00\x00P\x00\x00\x00\x01\x00\x0e\x02\xd0\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07c@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data[0x100:0x130] = b'\x00\x02X\x50\x00\x00\x00\x00\x00\x02X\x00\x00P\x00\x00\x00\x01\x00\x0e\x00`\x01\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\n2\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data[0x150:0x180] = b'\x00\x01^P\x00\x00\x00\x00\x00\x01^\x00\x00P\x00\x00\x00\x01\x00\x0e\x00\x38\x01\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x8a\xa0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data[0x1A0:0x1D0] = b'\x00\x01^P\x00\x00\x00\x00\x00\x01^\x00\x00P\x00\x00\x00\x01\x00\x0e\x00\x38\x01\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\r\xe8P\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data[0x5B:0x5C] = b'\x00'
        data[0xAB:0xAC] = b'\x01'
        data[0xFB:0xFC] = b'\x02'
        data[0x14B:0x14C] = b'\x03'
        data[0x19B:0x19C] = b'\x04'
        # Add three 0x00 bytes to the end of the file
        data.extend(b'\x00\x00\x00')

        with open(output_path, 'wb') as f:
            f.write(data)

    def modify_nut_file_dds(self, file_path, output_path):
        # Set replacement bytes to 00

        with open(file_path, 'rb') as f:
            data = bytearray(f.read())

        del data[0x0000:0x0280]

        # Given byte string
        byte_string = "4E 54 50 33 02 00 00 06 00 00 00 00 00 00 00 00 00 00 F0 40 00 00 00 00 00 00 EF D0 00 70 00 00 00 05 00 02 02 D0 00 40 00 00 00 00 00 00 00 00 00 00 02 80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 B4 00 00 00 2D 00 00 00 0B 40 00 00 02 D0 00 00 00 C0 00 00 00 00 00 00 00 00 00 00 00 00 65 58 74 00 00 00 00 20 00 00 00 10 00 00 00 00 47 49 44 58 00 00 00 10 00 00 00 00 00 00 00 00 00 01 86 10 00 00 00 00 00 01 85 A0 00 70 00 00 00 05 00 02 02 D0 00 68 00 00 00 00 00 00 00 00 00 00 F1 E0 00 00 00 00 00 00 00 00 00 00 00 00 00 01 24 80 00 00 49 20 00 00 12 50 00 00 04 A0 00 00 01 10 00 00 00 00 00 00 00 00 00 00 00 00 65 58 74 00 00 00 00 20 00 00 00 10 00 00 00 00 47 49 44 58 00 00 00 10 00 00 00 01 00 00 00 00 00 00 F0 40 00 00 00 00 00 00 EF D0 00 70 00 00 00 05 00 02 02 D0 00 40 00 00 00 00 00 00 00 00 00 02 77 10 00 00 00 00 00 00 00 00 00 00 00 00 00 00 B4 00 00 00 2D 00 00 00 0B 40 00 00 02 D0 00 00 00 C0 00 00 00 00 00 00 00 00 00 00 00 00 65 58 74 00 00 00 00 20 00 00 00 10 00 00 00 00 47 49 44 58 00 00 00 10 00 00 00 02 00 00 00 00 00 00 C8 50 00 00 00 00 00 00 C7 E0 00 70 00 00 00 05 00 02 00 60 01 90 00 00 00 00 00 00 00 00 00 03 66 70 00 00 00 00 00 00 00 00 00 00 00 00 00 00 96 00 00 00 25 80 00 00 09 60 00 00 02 60 00 00 00 A0 00 00 00 00 00 00 00 00 00 00 00 00 65 58 74 00 00 00 00 20 00 00 00 10 00 00 00 00 47 49 44 58 00 00 00 10 00 00 00 04 00 00 00 00 00 00 74 A0 00 00 00 00 00 00 74 40 00 60 00 00 00 04 00 02 00 38 01 90 00 00 00 00 00 00 00 00 00 04 2D E0 00 00 00 00 00 00 00 00 00 00 00 00 00 00 57 80 00 00 15 E0 00 00 05 80 00 00 01 60 65 58 74 00 00 00 00 20 00 00 00 10 00 00 00 00 47 49 44 58 00 00 00 10 00 00 00 04 00 00 00 00 00 00 74 A0 00 00 00 00 00 00 74 40 00 60 00 00 00 04 00 02 00 38 01 90 00 00 00 00 00 00 00 00 00 04 A1 C0 00 00 00 00 00 00 00 00 00 00 00 00 00 00 57 80 00 00 15 E0 00 00 05 80 00 00 01 60 65 58 74 00 00 00 00 20 00 00 00 10 00 00 00 00 47 49 44 58 00 00 00 10 00 00 00 05 00 00 00 00"

        # Convert the byte string into bytes
        bytes_data = bytes.fromhex(byte_string.replace(' ', ''))

        # Concatenate the bytes
        data = bytes_data + data

        with open(output_path, 'wb') as f:
            f.write(data)

def convert_png_to_dds(png_file, dds_file):
    # Ensure the input PNG file exists
    if not os.path.isfile(png_file):
        print(f"Error: {png_file} does not exist.")
        return False
    
    # Construct the command to convert using nvcompress
    command = [
        'nvcompress',  # Assuming nvcompress is in your PATH
        '-silent',     # Optional: Suppress output from nvcompress
        '-bc3',        # DXT5 compression (BC3 in nvcompress)
        '-alpha',      # Alpha Channel
        '-highest',      # Alpha Channel
        png_file,      # Input PNG file
        dds_file       # Output DDS file
    ]
    
    # Run the command using subprocess
    try:
        subprocess.run(command, check=True)
        print(f"Conversion successful: {png_file} -> {dds_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        return False

def convert_png_files_in_folder(input_folder, output_folder):
    # Ensure the input folder exists
    if not os.path.isdir(input_folder):
        print(f"Error: {input_folder} is not a valid directory.")
        return
    
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Iterate through files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".png"):
            input_path = os.path.join(input_folder, filename)
            output_filename = os.path.splitext(filename)[0] + ".dds"
            output_path = os.path.join(output_folder, output_filename)
            
            # Convert PNG to DDS
            success = convert_png_to_dds(input_path, output_path)
            
            if success:
                print(f"Conversion successful: {input_path} -> {output_path}")
            else:
                print(f"Conversion failed: {input_path}")

def load_png_to_texture(filepath):
    with Image.open(filepath) as img:
        img = img.convert("RGBA")
        width, height = img.size
        mipmap_data = img.tobytes()
        texture = NutTexture(width, height, "RGBA", "RGBA")
        texture.add_mipmap(mipmap_data)
        return texture

def read_dds_to_bytes(dds_file):
    try:
        with open(dds_file, "rb") as f:
            dds_bytes = f.read()
        return dds_bytes
    except FileNotFoundError:
        print(f"Error: File '{dds_file}' not found.")
        return None
    except Exception as e:
        print(f"Error reading DDS file '{dds_file}': {e}")
        return None

def load_dds_to_texture(filepath):
    with Image.open(filepath) as img:
        #img = img.convert("RGBA")
        width, height = img.size
        mipmap_data = read_dds_to_bytes(filepath)
        texture = NutTexture(width, height, "CompressedRgbaS3tcDxt5Ext", "CompressedRgbaS3tcDxt5Ext")
        #texture.add_mipmap(mipmap_data)
        return texture

def generate_nut_texture_dds(input_folder, output_file):
    nut = NUT()
    convert_png_files_in_folder(input_folder, input_folder)
    for filename in os.listdir(input_folder):
        if filename.endswith(".dds"):
            texture = load_dds_to_texture(os.path.join(input_folder, filename))
            nut.add_texture(texture)

    # Save the NUT file
    nut.save(output_file)

    # Modify the saved NUT file
    #nut.modify_nut_file(output_file, output_file)
    nut.modify_nut_file_dds(output_file, output_file)

def generate_nut_texture(input_folder, output_file):
    nut = NUT()
    for filename in os.listdir(input_folder):
        if filename.endswith(".png"):
            texture = load_png_to_texture(os.path.join(input_folder, filename))
            nut.add_texture(texture)

    # Save the NUT file
    nut.save(output_file)

    # Modify the saved NUT file
    nut.modify_nut_file(output_file, output_file)

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

def create_wiiu3_song_info_xml(song_info, current_unique_id, song_order, word_list):
    # Create the root element DB_DATA

    #db_data = ET.Element('DB_DATA', num=str(db_data_count))

    data_set = ET.Element('DATA_SET')
    
    def add_element(parent, tag, text):
        element = ET.SubElement(parent, tag)
        element.text = text
    
    song_id = song_info["id"]
    word_keys = [f"song_{song_id}", f"song_sub_{song_id}", f"song_detail_{song_id}"]
    
    word_info = None
    for key in word_keys:
        word_info = next((item for item in word_list["items"] if item["key"] == key), None)
        if word_info:
            break

    title = word_info.get("japaneseText", "") if word_info else ""

    # Combine "song_" with song_info["id"] to form the attribute value
    attribute_value = "song_" + str(song_info["id"])

    add_element(data_set, 'uniqueId', str(current_unique_id))
    add_element(data_set, 'id', song_info["id"])
    add_element(data_set, 'fumenFilePath', "/%AOC%/")
    add_element(data_set, 'songFilePath', "/%AOC%/sound/")
    add_element(data_set, 'songFileName', attribute_value)
    add_element(data_set, 'title', title)
    add_element(data_set, 'order', str(song_order))
        #Stupid fucking Genre fix for Vocaloid and Variety
    if str(song_info["genreNo"]) == "2":
        add_element(data_set, 'genreNo', "3")
    elif str(song_info["genreNo"]) == "3":
        add_element(data_set, 'genreNo', "2")
    else:
        add_element(data_set, 'genreNo', str(song_info["genreNo"]))
    add_element(data_set, 'songTitlePath', "/%AOC%/texture/")
    add_element(data_set, 'songWordsPath', " ")
    add_element(data_set, 'songWordsFileName', " ")
    add_element(data_set, 'secret', " ")
    add_element(data_set, 'releaseType', "0")
    add_element(data_set, 'ura', " ")
    add_element(data_set, 'dlc', "○")
    add_element(data_set, 'debug', " ")
    add_element(data_set, 'batonInterval', "2")
    add_element(data_set, 'isNotVsDuet', " ")
    if song_info["branchEasy"] == True:
        add_element(data_set, 'branchEasy', "○")
    else:
        add_element(data_set, 'branchEasy', "")
    if song_info["branchNormal"] == True:
        add_element(data_set, 'branchNormal', "○")
    else:
        add_element(data_set, 'branchNormal', "")
    if song_info["branchHard"] == True:
        add_element(data_set, 'branchHard', "○")
    else:
        add_element(data_set, 'branchHard', "")
    if song_info["branchMania"] == True:
        add_element(data_set, 'branchMania', "○")
    else:
        add_element(data_set, 'branchMania', "")
    add_element(data_set, 'starEasy', str(song_info["starEasy"]))
    add_element(data_set, 'starNormal', str(song_info["starNormal"]))
    add_element(data_set, 'starHard', str(song_info["starHard"]))
    add_element(data_set, 'starMania', str(song_info["starMania"]))
    add_element(data_set, 'donBg1pLumen', " ")
    add_element(data_set, 'donBg1pPath', " ")
    add_element(data_set, 'donBg2pLumen', " ")
    add_element(data_set, 'donBg2pPath', " ")
    add_element(data_set, 'chibiLumen', " ")
    add_element(data_set, 'chibiPath', " ")
    add_element(data_set, 'danceLumen', " ")
    add_element(data_set, 'dancePath', " ")
    add_element(data_set, 'danceNormalBgLumen', " ")
    add_element(data_set, 'danceNormalBgPath', " ")
    add_element(data_set, 'danceFeverBgLumen', " ")
    add_element(data_set, 'danceFeverBgPath', " ")
    add_element(data_set, 'danceDodaiLumen', " ")
    add_element(data_set, 'danceDodaiPath', " ")
    add_element(data_set, 'feverLumen', " ")
    add_element(data_set, 'feverPath', " ")
    add_element(data_set, 'rendaEffectLumen', " ")
    add_element(data_set, 'rendaEffectPath', " ")
    add_element(data_set, 'donBg1pLumen2', " ")
    add_element(data_set, 'donBg1pPath2', " ")
    add_element(data_set, 'donBg2pLumen2', " ")
    add_element(data_set, 'donBg2pPath2', " ")
    add_element(data_set, 'chibiLumen2', " ")
    add_element(data_set, 'chibiPath2', " ")
    add_element(data_set, 'danceLumen2', " ")
    add_element(data_set, 'dancePath2', " ")
    add_element(data_set, 'danceNormalBgLumen2', " ")
    add_element(data_set, 'danceNormalBgPath2', " ")
    add_element(data_set, 'danceFeverBgLumen2', " ")
    add_element(data_set, 'danceFeverBgPath2', " ")
    add_element(data_set, 'danceDodaiLumen2', " ")
    add_element(data_set, 'danceDodaiPath2', " ")
    add_element(data_set, 'feverLumen2', " ")
    add_element(data_set, 'feverPath2', " ")
    add_element(data_set, 'rendaEffectLumen2', " ")
    add_element(data_set, 'rendaEffectPath2', " ")
    
    return data_set

def create_wiiu3_song_info_extreme_xml(song_info, current_unique_id, song_order, word_list):
    # Create the root element DB_DATA

    #db_data = ET.Element('DB_DATA', num=str(db_data_count))

    data_set = ET.Element('DATA_SET')
    
    def add_element(parent, tag, text):
        element = ET.SubElement(parent, tag)
        element.text = text
    
    song_id = song_info["id"]
    word_keys = [f"song_{song_id}", f"song_sub_{song_id}", f"song_detail_{song_id}"]
    
    word_info = None
    for key in word_keys:
        word_info = next((item for item in word_list["items"] if item["key"] == key), None)
        if word_info:
            break

    title = word_info.get("japaneseText", "") if word_info else ""

    # Combine "song_" with song_info["id"] to form the attribute value
    attribute_value = "song_" + str(song_info["id"])

    add_element(data_set, 'uniqueId', str(current_unique_id))
    add_element(data_set, 'id', song_info["id"])
    add_element(data_set, 'fumenFilePath', "/%AOC%/")
    add_element(data_set, 'songFilePath', "/%AOC%/sound/")
    add_element(data_set, 'songFileName', attribute_value)
    add_element(data_set, 'title', title)
    add_element(data_set, 'order', str(song_order))
    #Stupid fucking Genre fix for Vocaloid and Variety
    if str(song_info["genreNo"]) == "2":
        add_element(data_set, 'genreNo', "3")
    elif str(song_info["genreNo"]) == "3":
        add_element(data_set, 'genreNo', "2")
    else:
        add_element(data_set, 'genreNo', str(song_info["genreNo"]))
    add_element(data_set, 'songTitlePath', "/%AOC%/texture/")
    add_element(data_set, 'songWordsPath', " ")
    add_element(data_set, 'songWordsFileName', " ")
    add_element(data_set, 'secret', " ")
    add_element(data_set, 'releaseType', "0")
    add_element(data_set, 'ura', "○")
    add_element(data_set, 'dlc', "○")
    add_element(data_set, 'debug', " ")
    add_element(data_set, 'batonInterval', "2")
    add_element(data_set, 'isNotVsDuet', " ")
    add_element(data_set, 'branchEasy', " ")
    add_element(data_set, 'branchNormal', " ")
    add_element(data_set, 'branchHard', " ")
    if song_info["branchMania"] == True:
        add_element(data_set, 'branchMania', "○")
    else:
        add_element(data_set, 'branchMania', "")
    add_element(data_set, 'starEasy', " ")
    add_element(data_set, 'starNormal', " ")
    add_element(data_set, 'starHard', " ")
    add_element(data_set, 'starMania', str(song_info["starMania"]))
    add_element(data_set, 'donBg1pLumen', " ")
    add_element(data_set, 'donBg1pPath', " ")
    add_element(data_set, 'donBg2pLumen', " ")
    add_element(data_set, 'donBg2pPath', " ")
    add_element(data_set, 'chibiLumen', " ")
    add_element(data_set, 'chibiPath', " ")
    add_element(data_set, 'danceLumen', " ")
    add_element(data_set, 'dancePath', " ")
    add_element(data_set, 'danceNormalBgLumen', " ")
    add_element(data_set, 'danceNormalBgPath', " ")
    add_element(data_set, 'danceFeverBgLumen', " ")
    add_element(data_set, 'danceFeverBgPath', " ")
    add_element(data_set, 'danceDodaiLumen', " ")
    add_element(data_set, 'danceDodaiPath', " ")
    add_element(data_set, 'feverLumen', " ")
    add_element(data_set, 'feverPath', " ")
    add_element(data_set, 'rendaEffectLumen', " ")
    add_element(data_set, 'rendaEffectPath', " ")
    add_element(data_set, 'donBg1pLumen2', " ")
    add_element(data_set, 'donBg1pPath2', " ")
    add_element(data_set, 'donBg2pLumen2', " ")
    add_element(data_set, 'donBg2pPath2', " ")
    add_element(data_set, 'chibiLumen2', " ")
    add_element(data_set, 'chibiPath2', " ")
    add_element(data_set, 'danceLumen2', " ")
    add_element(data_set, 'dancePath2', " ")
    add_element(data_set, 'danceNormalBgLumen2', " ")
    add_element(data_set, 'danceNormalBgPath2', " ")
    add_element(data_set, 'danceFeverBgLumen2', " ")
    add_element(data_set, 'danceFeverBgPath2', " ")
    add_element(data_set, 'danceDodaiLumen2', " ")
    add_element(data_set, 'danceDodaiPath2', " ")
    add_element(data_set, 'feverLumen2', " ")
    add_element(data_set, 'feverPath2', " ")
    add_element(data_set, 'rendaEffectLumen2', " ")
    add_element(data_set, 'rendaEffectPath2', " ")
    
    return data_set

def create_wiiu3_song_info_hard_xml(song_info, current_unique_id, song_order, word_list):
    # Create the root element DB_DATA

    #db_data = ET.Element('DB_DATA', num=str(db_data_count))

    data_set = ET.Element('DATA_SET')
    
    def add_element(parent, tag, text):
        element = ET.SubElement(parent, tag)
        element.text = text
    
    song_id = song_info["id"]
    word_keys = [f"song_{song_id}", f"song_sub_{song_id}", f"song_detail_{song_id}"]
    
    word_info = None
    for key in word_keys:
        word_info = next((item for item in word_list["items"] if item["key"] == key), None)
        if word_info:
            break

    title = word_info.get("japaneseText", "") if word_info else ""

    # Combine "song_" with song_info["id"] to form the attribute value
    attribute_value = "song_" + str(song_info["id"])

    add_element(data_set, 'uniqueId', str(current_unique_id))
    add_element(data_set, 'id', song_info["id"])
    add_element(data_set, 'fumenFilePath', "/%AOC%/")
    add_element(data_set, 'songFilePath', "/%AOC%/sound/")
    add_element(data_set, 'songFileName', attribute_value)
    add_element(data_set, 'title', title)
    add_element(data_set, 'order', str(song_order))
    #Stupid fucking Genre fix for Vocaloid and Variety
    if str(song_info["genreNo"]) == "2":
        add_element(data_set, 'genreNo', "3")
    elif str(song_info["genreNo"]) == "3":
        add_element(data_set, 'genreNo', "2")
    else:
        add_element(data_set, 'genreNo', str(song_info["genreNo"]))
    add_element(data_set, 'songTitlePath', "/%AOC%/texture/")
    add_element(data_set, 'songWordsPath', " ")
    add_element(data_set, 'songWordsFileName', " ")
    add_element(data_set, 'secret', " ")
    add_element(data_set, 'releaseType', "0")
    add_element(data_set, 'ura', "○")
    add_element(data_set, 'dlc', "○")
    add_element(data_set, 'debug', " ")
    add_element(data_set, 'batonInterval', "2")
    add_element(data_set, 'isNotVsDuet', " ")
    add_element(data_set, 'branchEasy', " ")
    add_element(data_set, 'branchNormal', " ")
    add_element(data_set, 'branchHard', " ")
    if song_info["branchHard"] == True:
        add_element(data_set, 'branchHard', "○")
    else:
        add_element(data_set, 'branchHard', "")
    add_element(data_set, 'starEasy', " ")
    add_element(data_set, 'starNormal', " ")
    add_element(data_set, 'starHard', " ")
    add_element(data_set, 'starMania', str(song_info["starHard"]))
    add_element(data_set, 'donBg1pLumen', " ")
    add_element(data_set, 'donBg1pPath', " ")
    add_element(data_set, 'donBg2pLumen', " ")
    add_element(data_set, 'donBg2pPath', " ")
    add_element(data_set, 'chibiLumen', " ")
    add_element(data_set, 'chibiPath', " ")
    add_element(data_set, 'danceLumen', " ")
    add_element(data_set, 'dancePath', " ")
    add_element(data_set, 'danceNormalBgLumen', " ")
    add_element(data_set, 'danceNormalBgPath', " ")
    add_element(data_set, 'danceFeverBgLumen', " ")
    add_element(data_set, 'danceFeverBgPath', " ")
    add_element(data_set, 'danceDodaiLumen', " ")
    add_element(data_set, 'danceDodaiPath', " ")
    add_element(data_set, 'feverLumen', " ")
    add_element(data_set, 'feverPath', " ")
    add_element(data_set, 'rendaEffectLumen', " ")
    add_element(data_set, 'rendaEffectPath', " ")
    add_element(data_set, 'donBg1pLumen2', " ")
    add_element(data_set, 'donBg1pPath2', " ")
    add_element(data_set, 'donBg2pLumen2', " ")
    add_element(data_set, 'donBg2pPath2', " ")
    add_element(data_set, 'chibiLumen2', " ")
    add_element(data_set, 'chibiPath2', " ")
    add_element(data_set, 'danceLumen2', " ")
    add_element(data_set, 'dancePath2', " ")
    add_element(data_set, 'danceNormalBgLumen2', " ")
    add_element(data_set, 'danceNormalBgPath2', " ")
    add_element(data_set, 'danceFeverBgLumen2', " ")
    add_element(data_set, 'danceFeverBgPath2', " ")
    add_element(data_set, 'danceDodaiLumen2', " ")
    add_element(data_set, 'danceDodaiPath2', " ")
    add_element(data_set, 'feverLumen2', " ")
    add_element(data_set, 'feverPath2', " ")
    add_element(data_set, 'rendaEffectLumen2', " ")
    add_element(data_set, 'rendaEffectPath2', " ")
    
    return data_set

def create_wiiu3_song_info_ura_xml(song_info, current_unique_id, song_order, word_list):
    # Create the root element DB_DATA

    #db_data = ET.Element('DB_DATA', num=str(db_data_count))

    data_set = ET.Element('DATA_SET')
    
    def add_element(parent, tag, text):
        element = ET.SubElement(parent, tag)
        element.text = text
    
    song_id = song_info["id"]
    word_keys = [f"song_{song_id}", f"song_sub_{song_id}", f"song_detail_{song_id}"]
    
    word_info = None
    for key in word_keys:
        word_info = next((item for item in word_list["items"] if item["key"] == key), None)
        if word_info:
            break

    title = word_info.get("japaneseText", "") if word_info else ""

    # Combine "song_" with song_info["id"] to form the attribute value
    attribute_value = "song_" + str(song_info["id"])

    add_element(data_set, 'uniqueId', str(current_unique_id))
    add_element(data_set, 'id', 'ex_' + song_info["id"])
    add_element(data_set, 'fumenFilePath', "/%AOC%/")
    add_element(data_set, 'songFilePath', "/%AOC%/sound/")
    add_element(data_set, 'songFileName', attribute_value)
    add_element(data_set, 'title', title)
    add_element(data_set, 'order', str(song_order))
    #Stupid fucking Genre fix for Vocaloid and Variety
    if str(song_info["genreNo"]) == "2":
        add_element(data_set, 'genreNo', "3")
    elif str(song_info["genreNo"]) == "3":
        add_element(data_set, 'genreNo', "2")
    else:
        add_element(data_set, 'genreNo', str(song_info["genreNo"]))
    add_element(data_set, 'songTitlePath', "/%AOC%/texture/")
    add_element(data_set, 'songWordsPath', " ")
    add_element(data_set, 'songWordsFileName', " ")
    add_element(data_set, 'secret', " ")
    add_element(data_set, 'releaseType', "0")
    add_element(data_set, 'ura', "○")
    add_element(data_set, 'dlc', "○")
    add_element(data_set, 'debug', " ")
    add_element(data_set, 'batonInterval', "2")
    add_element(data_set, 'isNotVsDuet', " ")
    add_element(data_set, 'branchEasy', " ")
    add_element(data_set, 'branchNormal', " ")
    add_element(data_set, 'branchHard', " ")
    if song_info["branchUra"] == True:
        add_element(data_set, 'branchMania', "○")
    else:
        add_element(data_set, 'branchMania', "")
    add_element(data_set, 'starEasy', " ")
    add_element(data_set, 'starNormal', " ")
    add_element(data_set, 'starHard', " ")
    add_element(data_set, 'starMania', str(song_info["starUra"]))
    add_element(data_set, 'donBg1pLumen', " ")
    add_element(data_set, 'donBg1pPath', " ")
    add_element(data_set, 'donBg2pLumen', " ")
    add_element(data_set, 'donBg2pPath', " ")
    add_element(data_set, 'chibiLumen', " ")
    add_element(data_set, 'chibiPath', " ")
    add_element(data_set, 'danceLumen', " ")
    add_element(data_set, 'dancePath', " ")
    add_element(data_set, 'danceNormalBgLumen', " ")
    add_element(data_set, 'danceNormalBgPath', " ")
    add_element(data_set, 'danceFeverBgLumen', " ")
    add_element(data_set, 'danceFeverBgPath', " ")
    add_element(data_set, 'danceDodaiLumen', " ")
    add_element(data_set, 'danceDodaiPath', " ")
    add_element(data_set, 'feverLumen', " ")
    add_element(data_set, 'feverPath', " ")
    add_element(data_set, 'rendaEffectLumen', " ")
    add_element(data_set, 'rendaEffectPath', " ")
    add_element(data_set, 'donBg1pLumen2', " ")
    add_element(data_set, 'donBg1pPath2', " ")
    add_element(data_set, 'donBg2pLumen2', " ")
    add_element(data_set, 'donBg2pPath2', " ")
    add_element(data_set, 'chibiLumen2', " ")
    add_element(data_set, 'chibiPath2', " ")
    add_element(data_set, 'danceLumen2', " ")
    add_element(data_set, 'dancePath2', " ")
    add_element(data_set, 'danceNormalBgLumen2', " ")
    add_element(data_set, 'danceNormalBgPath2', " ")
    add_element(data_set, 'danceFeverBgLumen2', " ")
    add_element(data_set, 'danceFeverBgPath2', " ")
    add_element(data_set, 'danceDodaiLumen2', " ")
    add_element(data_set, 'danceDodaiPath2', " ")
    add_element(data_set, 'feverLumen2', " ")
    add_element(data_set, 'feverPath2', " ")
    add_element(data_set, 'rendaEffectLumen2', " ")
    add_element(data_set, 'rendaEffectPath2', " ")
    
    return data_set

def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level + 1)
        if not subelem.tail or not subelem.tail.strip():
            subelem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def save_xml_to_file(xml_element, file_path):
    indent(xml_element)
    tree = ET.ElementTree(xml_element)
    tree.write(file_path, encoding='utf-8', xml_declaration=True)

# Initialize root element
root = ET.Element('DB_DATA')

# wii u file fuckery
def process_music_info(current_unique_id):
    # Define paths

    formatted_id = f"{current_unique_id:04d}"
    source_file = r'data\_resource\templates\musicInfo.drp'
    target_folder = rf'\out\content\{formatted_id}'
    executable_path = r'data\_resource\executable\DRPRepacker.exe'
    
    # Step 1: Copy file to target folder
    shutil.copy(source_file, os.getcwd() + target_folder)
    
    # Step 2: Run executable
    subprocess.run([executable_path, 'musicInfo.drp', 'musicInfo'], cwd=os.getcwd() + target_folder)
    
    # Step 3: Delete original file
    os.remove(os.getcwd() + target_folder + r'\musicInfo.drp')
    
    # Step 4: Rename repacked file
    os.rename(os.getcwd() + target_folder + r'\repacked.drp', os.getcwd() + target_folder + r'\musicInfo.drp')


def convert_endian(input_path, output_path, direction):
    ibo = obo = None  # in byte order, out byte order

    # Determine input and output byte order based on direction
    try:
        if direction.lower() == 'lb':
            ibo = '<'  # Little Endian
            obo = '>'  # Big Endian
        elif direction.lower() == 'bl':
            ibo = '>'  # Big Endian
            obo = '<'  # Little Endian
        else:
            raise ValueError(f'Invalid direction "{direction}"!')
    except ValueError as e:
        print(f'Error: {e}')
        return

    same_file = output_path == input_path

    if same_file:
        output_path += '.r'

    try:
        with open(input_path, 'rb') as fin:
            with open(output_path, 'wb') as fout:
                for hanteiI in range(36 * 3):
                    fout.write(struct.pack(obo + 'f', struct.unpack(ibo + 'f', fin.read(4))[0]))  # hantei notes

                while fin.tell() != 0x200:
                    fout.write(struct.pack(obo + 'I', struct.unpack(ibo + 'I', fin.read(4))[0]))  # header stuff like tamashii rate

                num_section = struct.unpack(ibo + 'I', fin.read(4))[0]
                fout.write(struct.pack(obo + 'I', num_section))  # num_section
                fout.write(struct.pack(obo + 'I', struct.unpack(ibo + 'I', fin.read(4))[0]))  # unknown

                for sectionI in range(num_section):
                    fout.write(struct.pack(obo + 'f', struct.unpack(ibo + 'f', fin.read(4))[0]))  # bpm
                    fout.write(struct.pack(obo + 'f', struct.unpack(ibo + 'f', fin.read(4))[0]))  # start_time
                    fout.write(struct.pack(obo + 'B', struct.unpack(ibo + 'B', fin.read(1))[0]))  # gogo
                    fout.write(struct.pack(obo + 'B', struct.unpack(ibo + 'B', fin.read(1))[0]))  # section_line
                    fout.write(struct.pack(obo + 'H', struct.unpack(ibo + 'H', fin.read(2))[0]))  # unknown

                    for bunkiI in range(6):
                        fout.write(struct.pack(obo + 'I', struct.unpack(ibo + 'I', fin.read(4))[0]))  # bunkis

                    fout.write(struct.pack(obo + 'I', struct.unpack(ibo + 'I', fin.read(4))[0]))  # unknown

                    for routeI in range(3):
                        num_notes = struct.unpack(ibo + 'H', fin.read(2))[0]
                        fout.write(struct.pack(obo + 'H', num_notes))  # num_notes
                        fout.write(struct.pack(obo + 'H', struct.unpack(ibo + 'H', fin.read(2))[0]))  # unknown
                        fout.write(struct.pack(obo + 'f', struct.unpack(ibo + 'f', fin.read(4))[0]))  # scroll

                        for noteI in range(num_notes):
                            note_type = struct.unpack(ibo + 'I', fin.read(4))[0]
                            fout.write(struct.pack(obo + 'I', note_type))  # note_type
                            fout.write(struct.pack(obo + 'f', struct.unpack(ibo + 'f', fin.read(4))[0]))  # headerI1
                            fout.write(struct.pack(obo + 'I', struct.unpack(ibo + 'I', fin.read(4))[0]))  # item
                            fout.write(struct.pack(obo + 'f', struct.unpack(ibo + 'f', fin.read(4))[0]))  # unknown1
                            fout.write(struct.pack(obo + 'H', struct.unpack(ibo + 'H', fin.read(2))[0]))  # hit
                            fout.write(struct.pack(obo + 'H', struct.unpack(ibo + 'H', fin.read(2))[0]))  # score_inc
                            fout.write(struct.pack(obo + 'f', struct.unpack(ibo + 'f', fin.read(4))[0]))  # length

                            if note_type in [6, 9, 98]:
                                fout.write(struct.pack(obo + 'I', struct.unpack(ibo + 'I', fin.read(4))[0]))  # unknown
                                fout.write(struct.pack(obo + 'I', struct.unpack(ibo + 'I', fin.read(4))[0]))  # unknown

        if same_file:
            shutil.move(output_path, input_path)

        print(f'Endian conversion completed: {input_path} -> {output_path}')

    except IOError as e:
        print(f'Error during file operation: {e}')

def process_fumens_files(fumen_output_dir):

    # Ensure fumen_output_dir ends with a slash for proper path joining
    if not fumen_output_dir.endswith('/'):
        fumen_output_dir += '/'

    # Regex pattern to match _1 or _2 in the file name
    duet_pattern = re.compile(r'_[12]\.bin$')

    for root, dirs, files in os.walk(fumen_output_dir):
        for file in files:
            if file.endswith('.bin'):
                input_path = os.path.join(root, file)
                output_dir = ''

                if duet_pattern.search(file):
                    # File contains _1 or _2, save to duet folder
                    output_dir = fumen_output_dir + 'duet/'
                else:
                    # File does not contain _1 or _2, save to solo folder
                    output_dir = fumen_output_dir + 'solo/'

                # Ensure the output directory exists, create if necessary
                os.makedirs(output_dir, exist_ok=True)

                # Construct output path
                output_path = os.path.join(output_dir, file)

                # Perform endian conversion (lb mode)
                convert_endian(input_path, output_path, 'lb')

def cleanup_fumen_output_dir(fumen_output_dir):
    # Ensure fumen_output_dir ends with a slash for proper path joining
    if not fumen_output_dir.endswith('/'):
        fumen_output_dir += '/'

    # List of directories to preserve
    preserve_dirs = ['solo', 'duet']

    # Iterate through all directories in fumen_output_dir
    for dir_name in os.listdir(fumen_output_dir):
        dir_path = os.path.join(fumen_output_dir, dir_name)

        # Check if it's a directory and not in the preserve list
        if os.path.isdir(dir_path) and dir_name not in preserve_dirs:
            try:
                # Clear out *.bin files in the directory
                bin_files = glob.glob(os.path.join(dir_path, '*.bin'))
                for bin_file in bin_files:
                    os.remove(bin_file)
                    print(f"Deleted file: {bin_file}")

                # Delete the directory and all its contents recursively
                shutil.rmtree(dir_path)
                print(f"Deleted directory: {dir_path}")
            except Exception as e:
                print(f"Error deleting {dir_path}: {e}")

def remove_musicinfo_leftover(directory_path):
    try:
        # Remove all files in the directory
        for file_path in glob.glob(os.path.join(directory_path, '*')):
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")

        # Delete the directory itself
        shutil.rmtree(directory_path)
        print(f"Deleted directory: {directory_path}")
    except Exception as e:
        print(f"Error deleting {directory_path}: {e}")


def remove_texture_leftover(texture_output_dir):
    try:
        # Iterate through all files and folders in texture_output_dir
        for path in glob.glob(os.path.join(texture_output_dir, '*')):
            if os.path.isfile(path):
                if path.endswith('.nut'):
                    # Skip *.nut files (preserve them)
                    continue
                else:
                    # Delete all other files
                    os.remove(path)
                    print(f"Deleted file: {path}")
            elif os.path.isdir(path):
                # Delete all directories (folders)
                shutil.rmtree(path)
                print(f"Deleted directory: {path}")

    except Exception as e:
        print(f"Error deleting files and folders in {texture_output_dir}: {e}")


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
    elif game_platform == "WIIU3":
        output_dir = "out/content/001A/musicInfo"
        fumen_output_dir = "out/content/001A/fumen"    
        audio_output_dir = "out/content/001A/sound"
        musicinfo_filename = "musicinfo.xml"
        texture_output_dir = "out/content/001A/texture"
        max_entries = 128  # Maximum allowed entries for NS1
        platform_tag = "wiiu3"        
    elif game_platform == "PTB":
        output_dir = "out/Data/Raw/ReadAssets"
        fumen_output_dir = "out/Data/Raw/fumen"
        audio_output_dir = "out/Data/Raw/sound/sound"
        musicinfo_filename = "musicinfo.json"
        songinfo_filename = "songinfo.json"
        max_entries = 200  # Maximum allowed entries for PTB
        platform_tag = "PTB"

    if game_platform == "WIIU3":
        print("")
    else:
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(fumen_output_dir, exist_ok=True)
        os.makedirs(audio_output_dir, exist_ok=True)

    selected_music_info = []
    selected_song_info = []    
    selected_wordlist = []
    current_unique_id = 0
    if game_platform == "WIIU3":
        current_unique_id = 500
        db_data_count = 0
        formatted_id = f"{current_unique_id:04d}"
        output_dir = f"out/content/{formatted_id}/musicInfo"
        fumen_output_dir = f"out/content/{formatted_id}/fumen"
        audio_output_dir = f"out/content/{formatted_id}/sound"
        texture_output_dir = f"out/content/{formatted_id}/texture"     

        def copy_fumens_ura():
            # Copy fumen folders for selected songs to output directory
            song_id = tree.item(item_id)["values"][1]
    
            # For default fumens
            fumen_folder_path = os.path.join(data_dir, "fumen", str(song_id))
            if os.path.exists(fumen_folder_path):
                for file_name in os.listdir(fumen_folder_path):
                    if file_name.endswith("_x.bin") or file_name.endswith("_x_1.bin") or file_name.endswith("_x_2.bin"):
                            original_path = os.path.join(fumen_folder_path, file_name)
                            new_name = "ex_" + file_name.replace("_x", "_m")
                            destination_path = os.path.join(fumen_output_dir, new_name)
                            shutil.copy2(original_path, destination_path)
                            print(f"Copied and renamed {file_name} to {new_name}")
                    
                # Retrieve song info from music_info
                song_info = next((item for item in music_info["items"] if item["id"] == song_id), None)
    
            # For custom fumens
            if custom_songs:
                custom_fumen_folder_path = os.path.join(custom_data_dir, "fumen", str(song_id))
                if os.path.exists(custom_fumen_folder_path):
                    for file_name in os.listdir(custom_fumen_folder_path):
                        if file_name.endswith("_x.bin") or file_name.endswith("_x_1.bin") or file_name.endswith("_x_2.bin"):
                            original_path = os.path.join(custom_fumen_folder_path, file_name)
                            new_name = "ex_" + file_name.replace("_x", "_m")
                            destination_path = os.path.join(fumen_output_dir, new_name)
                            shutil.copy2(original_path, destination_path)
                            print(f"Copied and renamed {file_name} to {new_name}")
                        
                    # Retrieve song info from custom_music_info
                    song_info = next((item for item in custom_music_info["items"] if item["id"] == song_id), None)

        def copy_fumens():
            # Copy fumen folders for selected songs to output directory
                song_id = tree.item(item_id)["values"][1]
                fumen_folder_path = os.path.join(data_dir, "fumen", str(song_id))
                if os.path.exists(fumen_folder_path):
                    if game_platform == "WIIU3":
                        shutil.copytree(fumen_folder_path, os.path.join(fumen_output_dir, f"{song_id}"))
                        print()
                    else:
                        shutil.copytree(fumen_folder_path, os.path.join(fumen_output_dir, f"{song_id}"))

        def copy_fumens_custom():
            # Copy fumen folders for selected songs to output directory
                song_id = tree.item(item_id)["values"][1]
                fumen_folder_path = os.path.join(custom_data_dir, "fumen", str(song_id))
                if os.path.exists(fumen_folder_path):
                    if game_platform == "WIIU3":
                        shutil.copytree(fumen_folder_path, os.path.join(fumen_output_dir, f"{song_id}"))
                        print()
                    else:
                        shutil.copytree(fumen_folder_path, os.path.join(fumen_output_dir, f"{song_id}"))                                    

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
        if game_platform == "WIIU3":
            print()
        else:
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

                if game_platform == "WIIU3":

                    pattern = r"^cs\d{4}$"

                    if re.match(pattern, song_info["id"]):
                        custom_songs == True
                    else:
                        custom_songs == False

                    #def convert_song_wiiu(song_id):
                    #    
                    #    preview_pos = get_preview_pos(song_id)
                    #    song_filename = os.path.join(data_dir, "sound", f"song_{song_id}.mp3")
                    #    output_file = os.path.join(audio_output_dir, f"song_{song_id}.nus3bank")

                    #    convert_audio_to_nus3bank(song_filename, "idsp", platform_tag, str(preview_pos), song_id)

                    #    if os.path.exists(f"song_{song_id}.nus3bank"):
                    #        shutil.move(f"song_{song_id}.nus3bank", output_file)
                    #        print(f"Created {output_file} successfully.")
                    #    else:
                    #        print(f"Conversion failed for song_{song_id}.")
                    #    if os.path.exists(f"song_{song_id}.mp3.idsp"):
                    #        os.remove(f"song_{song_id}.mp3.idsp")
                    #        print(f"Deleted song_{song_id}.mp3.idsp")        

                    def convert_song_wiiu(song_id, custom_songs):

                        preview_pos = get_preview_pos(song_id)

                        if custom_songs == True:
                            custom_preview_pos = get_preview_pos(song_id)

                        if custom_songs == True:
                            song_filename = os.path.join(custom_data_dir, "sound", f"song_{song_id}.mp3")
                        else:
                            song_filename = os.path.join(data_dir, "sound", f"song_{song_id}.mp3")

                        output_file = os.path.join(audio_output_dir, f"song_{song_id}.nus3bank")

                        convert_audio_to_nus3bank(song_filename, "idsp", platform_tag, str(preview_pos), song_id)
                        if os.path.exists(f"song_{song_id}.nus3bank"):
                            shutil.move(f"song_{song_id}.nus3bank", output_file)
                            print(f"Created {output_file} successfully.")
                        else:
                            print(f"Conversion failed for song_{song_id}.")
                        if os.path.exists(f"song_{song_id}.mp3.idsp"):
                            os.remove(f"song_{song_id}.mp3.idsp")
                            print(f"Deleted song_{song_id}.mp3.idsp")  

                    formatted_id = f"{current_unique_id:04d}"
                    output_dir = f"out/content/{formatted_id}/musicInfo"
                    fumen_output_dir = f"out/content/{formatted_id}/fumen"
                    audio_output_dir = f"out/content/{formatted_id}/sound"
                    texture_output_dir = f"out/content/{formatted_id}/texture"     

                    os.makedirs(output_dir, exist_ok=True)
                    os.makedirs(fumen_output_dir, exist_ok=True)
                    os.makedirs(audio_output_dir, exist_ok=True)

                    easy_value = int(song_info["starEasy"])
                    normal_value = int(song_info["starNormal"])
                    hard_value = int(song_info["starHard"])
                    extreme_value = int(song_info["starMania"]) 

                    if easy_value == 0 and normal_value == 0 and hard_value == 0 and extreme_value > 0:
                        print("Extreme Only Chart Detected")
                        wiiu3_song_info_xml = create_wiiu3_song_info_extreme_xml(song_info, current_unique_id, song_order, word_list)
                    elif easy_value == 0 and normal_value == 0 and extreme_value == 0 and hard_value > 0:
                        print("Hard Only Chart Detected") # this exists literally only for zzff14 lmao
                        wiiu3_song_info_xml = create_wiiu3_song_info_hard_xml(song_info, current_unique_id, song_order, word_list)
                    else:    
                        wiiu3_song_info_xml = create_wiiu3_song_info_xml(song_info, current_unique_id, song_order, word_list)

                    root.append(wiiu3_song_info_xml)

                    if re.match(pattern, song_info["id"]):
                        custom_songs == True
                        generate_wiiu3_texture(song_info["id"], song_info["genreNo"], current_unique_id, append_ura=False, custom_songs=True)
                    else:
                        custom_songs == False
                        generate_wiiu3_texture(song_info["id"], song_info["genreNo"], current_unique_id, append_ura=False, custom_songs=False)

                    file_path = f"out/content/{formatted_id}/musicInfo/musicinfo_db"
                    root.set('num', str(db_data_count))
                    save_xml_to_file(root, file_path)

                    if re.match(pattern, song_info["id"]):
                        custom_songs == True
                        copy_fumens_custom()
                    else:
                        custom_songs == False
                        copy_fumens()
                        
    
                    print(f"XML file saved to {file_path}")
                    process_music_info(current_unique_id)
                    print(f"DRP File generated")
                    process_fumens_files(fumen_output_dir)
                    print(f"Converted fumen files to big endian.")

                    input_folder = os.path.join(texture_output_dir, song_info["id"],)
                    output_file = os.path.join(texture_output_dir, f"{song_info['id']}.nut")
                    generate_nut_texture(input_folder, output_file)

                    if re.match(pattern, song_info["id"]):
                        custom_songs == True
                        convert_song_wiiu(song_id, custom_songs=True)
                    else:
                        custom_songs == False
                        convert_song_wiiu(song_id, custom_songs=False)

                    root.clear()

                    cleanup_fumen_output_dir(fumen_output_dir)
                    remove_musicinfo_leftover(output_dir)
                    remove_texture_leftover(texture_output_dir)

                    ura_value = int(song_info["starUra"])

                    if ura_value > 0:            

                        current_unique_id += 1
                        print(ura_value)

                        formatted_id = f"{current_unique_id:04d}"
                        output_dir = f"out/content/{formatted_id}/musicInfo"
                        fumen_output_dir = f"out/content/{formatted_id}/fumen"
                        audio_output_dir = f"out/content/{formatted_id}/sound"
                        texture_output_dir = f"out/content/{formatted_id}/texture"     

                        os.makedirs(output_dir, exist_ok=True)
                        os.makedirs(fumen_output_dir, exist_ok=True)
                        os.makedirs(audio_output_dir, exist_ok=True)

                        wiiu3_song_info_xml = create_wiiu3_song_info_ura_xml(song_info, current_unique_id, song_order, word_list)
                        root.append(wiiu3_song_info_xml)
                        if re.match(pattern, song_info["id"]):
                            custom_songs == True
                            generate_wiiu3_texture(song_info["id"], song_info["genreNo"], current_unique_id, append_ura=True, custom_songs=True)
                        else:
                            custom_songs == False
                            generate_wiiu3_texture(song_info["id"], song_info["genreNo"], current_unique_id, append_ura=True, custom_songs=False)

                        file_path = f"out/content/{formatted_id}/musicInfo/musicinfo_db"
                        root.set('num', str(db_data_count))
                        save_xml_to_file(root, file_path)

                        copy_fumens_ura()

                        print(f"XML file saved to {file_path}")
                        process_music_info(current_unique_id)
                        print(f"DRP File generated")
                        process_fumens_files(fumen_output_dir)
                        print(f"Converted fumen files to big endian.")
                        
                        input_folder = os.path.join(texture_output_dir, song_info["id"],)
                        output_file = os.path.join(texture_output_dir, f"ex_{song_info['id']}.nut")
                        generate_nut_texture(input_folder, output_file)
          
                        if re.match(pattern, song_info["id"]):
                            custom_songs == True
                            convert_song_wiiu(song_id, custom_songs=True)
                        else:
                            custom_songs == False
                            convert_song_wiiu(song_id, custom_songs=False)         

                        root.clear()    

                        cleanup_fumen_output_dir(fumen_output_dir)
                        remove_musicinfo_leftover(output_dir)
                        remove_texture_leftover(texture_output_dir)                          

                    if re.match(pattern, song_info["id"]):
                        custom_songs == True
                    else:
                        custom_songs == False

                elif game_platform == "NS1":
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
                if game_platform == "WIIU3":
                    db_data_count += 1

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

                elif game_platform == "WIIU3":
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
                        #convert_song(song_id, custom_songs)
                        print("")

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

        elif game_platform == "WIIU3":
            #file_path = f"out/content/001A/musicInfo/musicinfo_db"
            #root.set('num', str(db_data_count))
            #save_xml_to_file(root, file_path)
            #print(f"XML file saved to {file_path}")
            #process_music_info()
            #print(f"DRP File generated")
            #process_fumens_files(fumen_output_dir)
            #cleanup_fumen_output_dir(fumen_output_dir)
            print(f"Converted fumen files to big endian.")

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
    clear_button = ttk.Button(main_frame, text="クリア・セレクション", command=clear_selection)
else:
    clear_button = ttk.Button(main_frame, text="Clear Selection", command=clear_selection)
clear_button.pack(side="bottom", padx=20, pady=10)

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
game_platform_choices = ["PS4", "NS1", "WIIU3", "PTB"]
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
