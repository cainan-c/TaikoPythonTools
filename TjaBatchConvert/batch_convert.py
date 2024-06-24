import os
import json
import shutil
from pydub import AudioSegment
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import argparse
import logging
from threading import Lock

logging.basicConfig(level=logging.INFO)
json_lock = Lock()

# Define genre mapping
GENRE_MAPPING = {
    "J-POP": 0,
    "アニメ": 1,
    "VOCALOID": 2,
    "バラエティー": 3,
    "どうよう": 3,
    "クラシック": 5,
    "ゲームミュージック": 6,
    "ナムコオリジナル": 7
}

def get_genre_no(box_def_path):
    if not os.path.exists(box_def_path):
        return 3  # Default genre if box.def does not exist

    with open(box_def_path, "r", encoding="utf-8-sig") as file:
        for line in file:
            if line.startswith("#GENRE:"):
                genre = line.split(":")[1].strip()
                return GENRE_MAPPING.get(genre, 3)
    return 3

def parse_tja(tja_path):
    info = {}
    note_counts = {
        "Easy": 0,
        "Normal": 0,
        "Hard": 0,
        "Oni": 0,
        "Edit": 0
    }
    current_difficulty = None
    inside_notes_section = False
    
    difficulty_tags = {
        "Easy": "starEasy",
        "Normal": "starNormal",
        "Hard": "starHard",
        "Oni": "starMania",
        "Edit": "starUra"
    }
    
    with open(tja_path, "r", encoding="utf-8-sig") as file:
        for line in file:
            line = line.strip()
            if line.startswith("TITLE:"):
                info['TITLE'] = line.split(":")[1].strip()
            elif line.startswith("TITLEJA:"):
                info['TITLEJA'] = line.split(":")[1].strip()
            elif line.startswith("SUBTITLE:"):
                info['SUBTITLE'] = line.split(":")[1].strip()
            elif line.startswith("SUBTITLEJA:"):
                info['SUBTITLEJA'] = line.split(":")[1].strip()
            elif line.startswith("BPM:"):
                info['BPM'] = float(line.split(":")[1].strip())
            elif line.startswith("WAVE:"):
                info['WAVE'] = line.split(":")[1].strip()
            elif line.startswith("OFFSET:"):
                info['OFFSET'] = float(line.split(":")[1].strip())
            elif line.startswith("DEMOSTART:"):
                info['DEMOSTART'] = int(float(line.split(":")[1].strip()) * 1000)  # convert to ms
            elif line.startswith("COURSE:"):
                course = line.split(":")[1].strip()
                if course in difficulty_tags:
                    current_difficulty = course
                    inside_notes_section = False
            elif line.startswith("LEVEL:") and current_difficulty:
                info[difficulty_tags[current_difficulty]] = int(line.split(":")[1].strip())
            elif line.startswith("#START") and current_difficulty:
                inside_notes_section = True
            elif line.startswith("#END") and current_difficulty:
                inside_notes_section = False
                current_difficulty = None
            elif inside_notes_section and current_difficulty:
                note_counts[current_difficulty] += sum(line.count(ch) for ch in '1234')
    
    # Calculate shinuti and scores based on note counts
    for difficulty, count in note_counts.items():
        if difficulty in difficulty_tags and count > 0:
            tag = difficulty_tags[difficulty]
            shinuti = -(-1000000 // count)  # equivalent to math.ceil(1000000 / count)
            info[f'shinuti{difficulty}'] = shinuti
            info[f'shinuti{difficulty}Duet'] = shinuti
            info[f'score{difficulty}'] = shinuti * count
        else:
            tag = difficulty_tags[difficulty]
            info[f'shinuti{difficulty}'] = 0
            info[f'shinuti{difficulty}Duet'] = 0
            info[f'score{difficulty}'] = 0
    
    info['NOTE_COUNT'] = sum(note_counts.values())
    return info

def convert_audio(wave_path, output_path):
    audio = AudioSegment.from_file(wave_path)
    audio.export(output_path, format="mp3")

def append_to_json_file(filepath, data):
    with json_lock:
        try:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                existing_data["items"].append(data)
            else:
                existing_data = {"items": [data]}
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
            #logging.info(f"Appended data to {filepath} successfully.")
        except json.JSONDecodeError as e:
            logging.error(f"JSON decoding error while processing {filepath}: {e}")
            raise
        except Exception as e:
            logging.error(f"Error while appending data to {filepath}: {e}")
            raise

def append_to_json_list_file(filepath, data):
    with json_lock:
        try:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                existing_data.append(data)
            else:
                existing_data = [data]
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
            #logging.info(f"Appended data to {filepath} successfully.")
        except json.JSONDecodeError as e:
            logging.error(f"JSON decoding error while processing {filepath}: {e}")
            raise
        except Exception as e:
            logging.error(f"Error while appending data to {filepath}: {e}")
            raise

def create_json_files(info, genre_no, unique_id, output_dir):
    musicinfo = {
        "uniqueId": unique_id,
        "id": f"cs{unique_id:04d}",
        "songFileName": f"sound/song_cs{unique_id:04d}",
        "order": unique_id,
        "genreNo": genre_no,
        "branchEasy": False,
        "branchNormal": False,
        "branchHard": False,
        "branchMania": False,
        "branchUra": False,
        "starEasy": info.get("starEasy", 0),
        "starNormal": info.get("starNormal", 0),
        "starHard": info.get("starHard", 0),
        "starMania": info.get("starMania", 0),
        "starUra": info.get("starUra", 0),
        "shinutiEasy": info.get("shinutiEasy", 0),
        "shinutiNormal": info.get("shinutiNormal", 0),
        "shinutiHard": info.get("shinutiHard", 0),
        "shinutiMania": info.get("shinutiOni", 0),
        "shinutiUra": info.get("shinutiUra", 0),
        "shinutiEasyDuet": info.get("shinutiEasyDuet", 0),
        "shinutiNormalDuet": info.get("shinutiNormalDuet", 0),
        "shinutiHardDuet": info.get("shinutiHardDuet", 0),
        "shinutiManiaDuet": info.get("shinutiOniDuet", 0),
        "shinutiUraDuet": info.get("shinutiEditDuet", 0),
        "scoreEasy": info.get("scoreEasy", 0),
        "scoreNormal": info.get("scoreNormal", 0),
        "scoreHard": info.get("scoreHard", 0),
        "scoreMania": info.get("scoreOni", 0),
        "scoreUra": info.get("scoreEdit", 0)
    }

    previewpos = {
        "id": f"cs{unique_id:04d}",
        "previewPos": info['DEMOSTART']
    }

    wordlist = {
        "key": f"song_cs{unique_id:04d}",
        "japaneseText": info['TITLE'],
        "japaneseFontType": 0,
        "englishUsText": info['TITLE'],
        "englishUsFontType": 1,
        "chineseTText": info['TITLE'],
        "chineseTFontType": 0,
        "koreanText": info['TITLE'],
        "koreanFontType": 0
    }

    wordlist_sub = {
        "key": f"song_sub_cs{unique_id:04d}",
        "japaneseText": info.get('SUBTITLE', ''),
        "japaneseFontType": 0,
        "englishUsText": info.get('SUBTITLE', ''),
        "englishUsFontType": 1,
        "chineseTText": info.get('SUBTITLE', ''),
        "chineseTFontType": 0,
        "koreanText": info.get('SUBTITLE', ''),
        "koreanFontType": 0
    }

    wordlist_detail = {
        "key": f"song_detail_cs{unique_id:04d}",
        "japaneseText": "",
        "japaneseFontType": 0,
        "englishUsText": "",
        "englishUsFontType": 1,
        "chineseTText": "",
        "chineseTFontType": 0,
        "koreanText": "",
        "koreanFontType": 0
    }

    append_to_json_file(os.path.join(output_dir, "datatable/musicinfo.json"), musicinfo)
    append_to_json_list_file(os.path.join(output_dir, "datatable/previewpos.json"), previewpos)
    append_to_json_file(os.path.join(output_dir, "datatable/wordlist.json"), wordlist)
    append_to_json_file(os.path.join(output_dir, "datatable/wordlist.json"), wordlist_sub)
    append_to_json_file(os.path.join(output_dir, "datatable/wordlist.json"), wordlist_detail)

def convert_tja_to_fumen(tja_path):
    subprocess.run(["bin/tja2fumen", tja_path], check=True)

def move_and_rename_bin_files(tja_path, output_dir, unique_id):
    base_dir = os.path.dirname(tja_path)
    output_path = os.path.join(output_dir, f"fumen/cs{unique_id:04d}")
    os.makedirs(output_path, exist_ok=True)

    difficulties = ["_e", "_n", "_h", "_x", "_m"]
    any_bin_file_moved = False

    for difficulty in difficulties:
        bin_file = f"{os.path.splitext(tja_path)[0]}{difficulty}.bin"
        if os.path.exists(bin_file):
            shutil.move(bin_file, os.path.join(output_path, f"cs{unique_id:04d}{difficulty}.bin"))
            any_bin_file_moved = True

    if not any_bin_file_moved:
        # Move the generic .bin file as cs{unique_id:04d}_m.bin
        generic_bin_file = f"{os.path.splitext(tja_path)[0]}.bin"
        if os.path.exists(generic_bin_file):
            shutil.move(generic_bin_file, os.path.join(output_path, f"cs{unique_id:04d}_m.bin"))

def process_song_charts(dir_path, file, output_folder, unique_id):
    tja_path = os.path.join(dir_path, file)
    convert_tja_to_fumen(tja_path)
    move_and_rename_bin_files(tja_path, output_folder, unique_id)

def process_song_metadata(dir_path, file, genre_no, unique_id, output_folder):
    tja_path = os.path.join(dir_path, file)
    info = parse_tja(tja_path)
    create_json_files(info, genre_no, unique_id, output_folder)

#def process_song_audio(dir_path, file, unique_id, output_folder):
#    tja_path = os.path.join(dir_path, file)
#    info = parse_tja(tja_path)
#    convert_audio(os.path.join(dir_path, info['WAVE']), os.path.join(output_folder, f"sound/song_cs{unique_id:04d}.mp3"))

def process_song_audio(dir_path, file, unique_id, output_folder):
    tja_path = os.path.join(dir_path, file)
    info = parse_tja(tja_path)
    convert_audio(os.path.join(dir_path, info['WAVE']), os.path.join(output_folder, f"sound/song_cs{unique_id:04d}.mp3"))

def process_songs_multithreaded(dir_path, files, output_folder):
    with ThreadPoolExecutor() as executor:
        futures = []
        for unique_id, file in enumerate(files):
            futures.append(executor.submit(process_song_audio, dir_path, file, unique_id, output_folder))
        
        # Optionally, wait for all futures to complete
        for future in futures:
            future.result()



def process_song(dir_path, file, genre_no, unique_id, output_folder):
    try:
        process_song_audio(dir_path, file, unique_id, output_folder)
        process_song_charts(dir_path, file, output_folder, unique_id)
        process_song_metadata(dir_path, file, genre_no, unique_id, output_folder)
        #logging.info(f"Processed {file} successfully.")
    except Exception as e:
        logging.error(f"Failed to process {file} in {dir_path}: {e}")

def main(input_folder, output_folder):
    unique_id = 1
    
    for root, dirs, files in os.walk(input_folder):
        if "box.def" in files:
            genre_no = get_genre_no(os.path.join(root, "box.def"))
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                tja_files = [file for file in os.listdir(dir_path) if file.endswith(".tja")]
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = [
                        executor.submit(process_song, dir_path, file, genre_no, unique_id + i, output_folder)
                        for i, file in enumerate(tja_files)
                    ]
                    
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            future.result()
                            unique_id += 1
                        except Exception as e:
                            logging.error(f"Error in future: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process TJA files and generate related files.")
    parser.add_argument("input_folder", help="The input folder containing TJA files.")
    parser.add_argument("output_folder", help="The output folder where processed files will be saved.")
    
    args = parser.parse_args()
    
    os.makedirs(args.output_folder, exist_ok=True)
    os.makedirs(os.path.join(args.output_folder, "sound"), exist_ok=True)
    os.makedirs(os.path.join(args.output_folder, "datatable"), exist_ok=True)
    
    main(args.input_folder, args.output_folder)
