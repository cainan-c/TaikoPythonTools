import json
import shutil
import os
import toml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def copy_sound_file(song_id, source_folder, output_folder):
    # Source path for song_[id].nus3bank
    source_sound_file = os.path.join(source_folder, "sound", f"song_{song_id}.nus3bank")
    
    # Destination path in output_folder/sound
    destination_sound_file = os.path.join(output_folder, "sound", f"song_{song_id}.nus3bank")

    # Copy sound/song_[id].nus3bank to output_folder/sound/song_[id].nus3bank
    if os.path.exists(source_sound_file):
        os.makedirs(os.path.join(output_folder, "sound"), exist_ok=True)
        shutil.copy2(source_sound_file, destination_sound_file)

        # Log message based on game origin
        game_origin = os.path.basename(os.path.normpath(source_folder))
        if game_origin in ["JPN00", "JPN08"]:
            logger.info(f"Copied song_{song_id}.nus3bank from '{game_origin}'.")

def process_added_songs(json_file, config_file):
    with open(json_file, 'r') as f:
        added_songs = json.load(f)

    config = toml.load(config_file)
    output_folder = config['output']['folder']
    
    for song in added_songs:
        song_id = song.get('id')
        game_origin = song.get('gameOrigin')
        
        if game_origin in config['game_origin_mapping']:
            source_folder = config['game_origin_mapping'][game_origin]
            copy_sound_file(song_id, source_folder, output_folder)

# Specify the paths to your JSON and TOML files
json_file_path = 'added_songs.json'
config_file_path = 'config.toml'

# Call the function to process the added songs using the specified configuration
process_added_songs(json_file_path, config_file_path)
