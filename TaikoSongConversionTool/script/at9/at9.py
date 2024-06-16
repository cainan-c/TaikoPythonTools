import subprocess
import os
import sys
import shutil
import tempfile
from pydub import AudioSegment

def convert_audio_to_at9(input_file, output_file):
    # Create a temporary folder to store intermediate files
    temp_folder = tempfile.mkdtemp()
    os.makedirs(temp_folder, exist_ok=True)

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
        at9tool_cli_path = os.path.join("bin", "at9tool.exe")

        # Run VGAudioCli to convert WAV to AT9
        subprocess.run([at9tool_cli_path, "-e", "-br", "192", input_file, output_file], check=True)

    finally:
        # Clean up temporary folder
        shutil.rmtree(temp_folder, ignore_errors=True)
        
if __name__ == "__main__":
    # Check command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python at9.py <input_file> <output_file>")
        sys.exit(1)

    input_audio_file = sys.argv[1]
    output_audio_file = sys.argv[2]

    try:
        convert_audio_to_at9(input_audio_file, output_audio_file)
        print(f"Conversion successful. Output file: {output_audio_file}")
    except Exception as e:
        print(f"Error during conversion: {e}")
