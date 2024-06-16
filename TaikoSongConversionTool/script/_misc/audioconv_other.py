import os
import sys
import subprocess
import concurrent.futures
from pydub import AudioSegment

# Function to process each .nus3bank file
def process_nus3bank(file):
    if file.endswith('.nus3bank'):
        base_name = os.path.splitext(os.path.basename(file))[0]
        out_folder = "out"
        wav_file = os.path.join(out_folder, f"{base_name}.wav")
        command = f"vgmstream-cli.exe -o {wav_file} {file}"
        subprocess.run(command, shell=True, check=True)

        # Trim the first 20ms and convert to flac
        process_wav_with_trim(wav_file)

# Function to process each .wav file by trimming and converting to .flac
def process_wav_with_trim(wav_file):
    if wav_file.endswith('.wav'):
        audio = AudioSegment.from_wav(wav_file)

        trimmed_audio = audio[0:]
        
        base_name = os.path.splitext(os.path.basename(wav_file))[0]
        out_folder = "out"
        flac_file = os.path.join(out_folder, f"{base_name}.flac")
        
        # Export trimmed audio to compressed FLAC with specified sample rate (48000 Hz)
        trimmed_audio.export(flac_file, format="flac", parameters=["-ar", "48000", "-compression_level", "8"])

        # Clean up .wav file
        os.remove(wav_file)

# Main function
def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py path/to/input/folder")
        return
    
    input_folder = sys.argv[1]

    # Check if the input folder exists
    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' not found.")
        return

    out_folder = "out"
    
    # Create output folder if it doesn't exist
    os.makedirs(out_folder, exist_ok=True)

    # List all .nus3bank files in the input folder
    nus3bank_files = [os.path.join(input_folder, file) for file in os.listdir(input_folder) if file.endswith('.nus3bank')]

    # Process files using a thread pool with 5 worker threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Submit each file processing task to the executor
        futures = [executor.submit(process_nus3bank, file) for file in nus3bank_files]

        # Wait for all tasks to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()  # This will propagate exceptions if any occurred during execution
            except Exception as exc:
                print(f"An error occurred: {exc}")

if __name__ == "__main__":
    main()
