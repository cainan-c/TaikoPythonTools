import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import subprocess
import shutil
import gzip
import concurrent.futures
import functools
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

# Function to load configuration from file
def load_config():
    config_file = "config.json"
    default_config = {
        "max_concurrent": 5,  # Default value if not specified in config file
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
# custom_song_path = config["custom_path"]

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

genre_map = {
    0: ("POP", "light blue"),
    1: ("Anime", "orange"),
    2: ("Vocaloid", "turquoise"),
    3: ("Variety", "green"),
    4: ("Unused", "gray"),
    5: ("Classic", "dark red"),
    6: ("Game Music", "purple"),
    7: ("Namco Original", "dark orange"),
}

song_titles = {item["key"]: item["englishUsText"] for item in word_list["items"]}
song_subtitles = {item["key"]: item["englishUsText"] for item in word_list["items"]}

if custom_songs == True:
    custom_song_titles = {item["key"]: item["englishUsText"] for item in custom_word_list["items"]}
    custom_song_subtitles = {item["key"]: item["englishUsText"] for item in custom_word_list["items"]}

window = tk.Tk()
window.title("Taiko no Tatsujin Song Conversion GUI Tool")

# Set the initial size of the window
window.geometry("1000x600")  # Width x Height

# Create Treeview and Scrollbar
tree = ttk.Treeview(window, columns=("Select", "Unique ID", "ID", "Song Name", "Song Subtitle", "Genre", "Difficulty"), show="headings")
tree.heading("Unique ID", text="")
tree.heading("ID", text="ID")
tree.heading("Song Name", text="Song Name")
tree.heading("Song Subtitle", text="Song Subtitle")
tree.heading("Genre", text="Genre")
tree.heading("Difficulty", text="Difficulty")
tree.heading("Select", text="Select")

tree.column("Select", width=50, anchor=tk.CENTER)
tree.column("Unique ID", width=0, anchor=tk.W)
tree.column("ID", width=60, anchor=tk.W)
tree.column("Song Name", anchor=tk.W)
tree.column("Song Subtitle", anchor=tk.W)
tree.column("Genre",  width=100, anchor=tk.W)
tree.column("Difficulty", width=120, anchor=tk.W)

vsb = ttk.Scrollbar(window, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=vsb.set)

# Pack Treeview and Scrollbar
tree.pack(side="left", padx=10, pady=10, fill="both", expand=True)
vsb.pack(side="left", fill="y", padx=(0, 10), pady=10)

# Counter for selected items
selection_count = tk.IntVar()
selection_count.set(0)  # Initial selection count

def on_search_keyrelease(event):
    print("Key released:", event.keysym)
    #filter_treeview()

# Create Search Entry
search_var = tk.StringVar()
search_entry = ttk.Entry(window, textvariable=search_var)

def toggle_checkbox(event):
    # Get the item_id based on the event coordinates
    item_id = tree.identify_row(event.y)

    # Ensure item_id is valid and corresponds to a valid item in the tree
    if item_id and tree.exists(item_id):
        current_state = item_selection_state.get(item_id, "☐")

        if current_state == "☐":
            new_state = "☑"
        elif current_state == "☑":
            new_state = "☐"

        # Update the selection state for the item
        item_selection_state[item_id] = new_state

        # Update the values in the treeview to reflect the new state
        tree.item(item_id, values=(new_state,) + tree.item(item_id, "values")[1:])

        # Update the selection count based on the state change
        if new_state == "☑":
            selection_count.set(selection_count.get() + 1)  # Increment selection count
        elif new_state == "☐":
            selection_count.set(selection_count.get() - 1)  # Decrement selection count

def filter_treeview():
    search_text = search_var.get().strip().lower()
    populate_tree(search_text)  # Populate Treeview with filtered data
    
def populate_tree():
    global selected_items  # Use global variable to persist selection state

    # Store currently selected items
    current_selection = tree.selection()

    # Clear existing items in the Treeview
    tree.delete(*tree.get_children())

    for song in sorted(music_info["items"], key=lambda x: x["id"]):  # Sort by ID
        unique_id = ""
        song_id = f"{song['id']}"
        genre_no = song["genreNo"]
        genre_name, genre_color = genre_map.get(genre_no, ("Unknown Genre", "white"))
        english_title = song_titles.get(f"song_{song_id}", "-")
        english_subtitle = song_subtitles.get(f"song_sub_{song_id}", "-")

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

        # Check if the search text matches the song name
        if search_var.get().strip().lower() in english_title.lower():
            item_id = tree.insert("", "end", values=("☐", unique_id, song_id, english_title, english_subtitle, genre_name, difficulty_info))
            tree.tag_configure(genre_name, background=genre_color)

    if custom_songs == True:
        for song in sorted(custom_music_info["items"], key=lambda x: x["id"]):  # Sort by ID
            unique_id = ""
            song_id = f"{song['id']}"
            genre_no = song["genreNo"]
            genre_name, genre_color = genre_map.get(genre_no, ("Unknown Genre", "white"))
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

            # Check if the search text matches the song name
            if search_var.get().strip().lower() in english_title.lower():
                item_id = tree.insert("", "end", values=("☐", unique_id, song_id, english_title, english_subtitle, genre_name, difficulty_info))
                tree.tag_configure(genre_name, background=genre_color)


    # Restore original selection after filtering
    for item in current_selection:
        if tree.exists(item):  # Check if item exists in Treeview
            tree.selection_add(item)
        else:
            print("Item not found:", item)  # Debug print

search_entry.bind("<KeyRelease>", lambda event: populate_tree())

def sort_tree(sort_option):
    # Clear existing items in the Treeview
    for item in tree.get_children():
        tree.delete(item)

    if sort_option == "ID":
        populate_tree()  # Sort by ID
        selection_count.set(0)  # Reset Counter to 0
    elif sort_option == "Song Name":
        selection_count.set(0)  # Reset Counter to 0
        for song in sorted(music_info["items"], key=lambda x: song_titles.get(f"song_{x['id']}", "-")):
            populate_song_entry(song)
        if custom_songs == True:
            for song in sorted(custom_music_info["items"], key=lambda x: custom_song_titles.get(f"song_{x['id']}", "-")):
                populate_song_entry(song)
    elif sort_option == "Genre":
        selection_count.set(0)  # Reset Counter to 0
        for genre_no in sorted(genre_map.keys()):
            for song in sorted(music_info["items"], key=lambda x: x["id"]):
                if song["genreNo"] == genre_no:
                    populate_song_entry(song)
            if custom_songs == True:
                for song in sorted(custom_music_info["items"], key=lambda x: x["id"]):
                    if song["genreNo"] == genre_no:
                        populate_song_entry(song)

def populate_song_entry(song):
    unique_id = ""
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

    item_id = tree.insert("", "end", values=("☐", unique_id, song_id, english_title, english_subtitle, genre_name, difficulty_info))
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
tree.bind("<Button-1>", toggle_checkbox)
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
    # Load previewpos data from the default file
    with open(previewpos_path, "r", encoding="utf-8") as previewpos_file:
        previewpos_data = json.load(previewpos_file)
        for item in previewpos_data:
            if item["id"] == song_id:
                return item["previewPos"]
    
    # If use_custom is True, also try to load from the custom file
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
        song_id = tree.item(selected_item[0])["values"][2]
        preview_audio(song_id)

def merge_ptb():
    command = [
        "python",
        "script/ptb_wordlist.py",                        
        ]
    subprocess.run(command)

def merge_ps4_int():
    command = [
        "python",
        "script/ps4_wordlist.py",                        
        ]
    subprocess.run(command)

def merge_ps4_jp():
    command = [
        "python",
        "script/ps4_wordlist_jp.py",                        
        ]
    subprocess.run(command)

def merge_ns1_int():
    command = [
        "python",
        "script/ns1_wordlist.py",                        
        ]
    subprocess.run(command)

def merge_ns1_jp():
    command = [
        "python",
        "script/ns1_wordlist_jp.py",                        
        ]
    subprocess.run(command)

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
            song_id = tree.item(item_id)["values"][2]
            fumen_folder_path = os.path.join(data_dir, "fumen", str(song_id))
            if os.path.exists(fumen_folder_path):
                shutil.copytree(fumen_folder_path, os.path.join(fumen_output_dir, f"{song_id}"))

            song_info = next((item for item in music_info["items"] if item["id"] == song_id), None)

        if custom_songs:
            for item_id in selected_items:

                song_id = tree.item(item_id)["values"][2]
                custom_fumen_folder_path = os.path.join(custom_data_dir, "fumen", str(song_id))
                if os.path.exists(custom_fumen_folder_path):
                    shutil.copytree(custom_fumen_folder_path, os.path.join(fumen_output_dir, f"{song_id}"))

                song_info = next((item for item in custom_music_info["items"] if item["id"] == song_id), None)

        for item_id in selected_items:
            song_id = tree.item(item_id)["values"][2]
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
                        command = [
                            "python",
                            "conv.py",
                            song_filename,
                            "at9",
                            platform_tag,
                            str(preview_pos),  # Convert preview_pos to string
                            song_id
                        ]
                        subprocess.run(command)
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
                        command = [
                            "python",
                            "script/acb/acb.py",
                            song_filename,
                            song_id
                        ]
                        subprocess.run(command)
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
                        command = [
                            "python",
                            "conv.py",
                            song_filename,
                            "idsp",
                            platform_tag,
                            str(preview_pos),  # Convert preview_pos to string
                            song_id
                        ]
                        subprocess.run(command)
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

            merge_ptb()

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
                merge_ps4_jp()
            elif game_region == "EU/USA":
                merge_ps4_int()

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
                merge_ns1_jp()
            elif game_region == "EU/USA":
                merge_ns1_int()


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

preview_button = ttk.Button(window, text="Preview", command=preview_selected)
preview_button.pack(side="top", padx=20, pady=10)

# Create sorting options
sort_options = ["ID", "Song Name", "Genre"]
sort_label = tk.Label(window, text="Sort by:")
sort_label.pack(side="top", padx=20, pady=5)

sort_var = tk.StringVar(window)
sort_var.set("ID")
sort_menu = tk.OptionMenu(window, sort_var, *sort_options, command=lambda _: sort_tree(sort_var.get()))
sort_menu.pack(side="top", padx=20, pady=0)

# search_entry.pack(side="top", padx=20, pady=10, fill="x") # search bar, currently broken

# Bottom Side

export_button = ttk.Button(window, text="Export", command=export_data)
export_button.pack(side="bottom", padx=20, pady=10)

# Create Selection Count Label
selection_count_label = ttk.Label(window, text="0/???")
selection_count_label.pack(side="bottom", padx=20, pady=10)

game_platform_var = tk.StringVar(window)
game_platform_var.set("PS4")
game_platform_choices = ["PS4", "NS1", "PTB"]
game_platform_menu = tk.OptionMenu(window, game_platform_var, *game_platform_choices)
game_platform_menu.pack(side="bottom", padx=20, pady=0)

# Create Label for Platform selection
platform_label = tk.Label(window, text="Platform")
platform_label.pack(side="bottom", padx=20, pady=5)

# Game region selection, needed for wordlist export.
game_region_var = tk.StringVar(window)
game_region_var.set("JPN/ASIA")
game_region_choices = ["JPN/ASIA", "EU/USA"]
game_region_menu = tk.OptionMenu(window, game_region_var, *game_region_choices)
game_region_menu.pack(side="bottom", padx=20, pady=10)

game_region_label = tk.Label(window, text="Game Region:")
game_region_label.pack(side="bottom", padx=20, pady=0)

# Doesn't function?
# Update selection count when tree selection changes
#tree.bind("<<TreeviewSelect>>", lambda event: update_selection_count())

window.mainloop()
