import argparse
import subprocess
import os
import sys

def convert_audio_to_nus3bank(input_audio, audio_type, game, preview_point, song_id):
    # Determine the output filename for the nus3bank
    output_filename = f"song_{song_id}.nus3bank"
    converted_audio_file = f"{input_audio}.{audio_type}"

    # Determine the path to the run.py script within the 'script' folder
    templates_folder = os.path.join(os.path.dirname(__file__), 'script')
    run_py_path = os.path.join(templates_folder, 'run.py')

    # Prepare the command based on the audio type
    if audio_type in ["bnsf", "at9", "idsp", "lopus", "wav"]:
        # Construct the command to convert input audio to the specified type
        conversion_command = ["python", run_py_path, audio_type, input_audio, f"{input_audio}.{audio_type}"]

        # Construct the command to create the nus3bank
        nus3_command = ["python", run_py_path, "nus3", game, f"{input_audio}.{audio_type}", str(preview_point), output_filename]

        try:
            # Execute the conversion command
            subprocess.run(conversion_command, check=True)

            # Execute the nus3 command
            subprocess.run(nus3_command, check=True)

            print(f"Conversion successful! Created {output_filename}")

            # Delete the non-nus3bank file after successful conversion
            if os.path.exists(converted_audio_file):
                os.remove(converted_audio_file)
                print(f"Deleted {converted_audio_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
    else:
        print(f"Unsupported audio type: {audio_type}")

def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Convert audio to nus3bank")

    # Define command-line arguments
    parser.add_argument("input_audio", type=str, nargs="?", help="Input audio file path.")
    parser.add_argument("audio_type", type=str, nargs="?", help="Type of input audio (e.g., wav, bnsf, at9, idsp, lopus).")
    parser.add_argument("game", type=str, nargs="?", help="Game type (e.g., nijiiro, ns1, ps4, wiiu3).")
    parser.add_argument("preview_point", type=int, nargs="?", help="Audio preview point in ms.")
    parser.add_argument("song_id", type=str, nargs="?", help="Song ID for the nus3bank file.")

    # Parse the command-line arguments
    args = parser.parse_args()

    # If no arguments are provided, display usage information
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    # Validate input audio file path
    if not args.input_audio:
        print("Error: Input audio file path is required.")
        parser.print_help()
        sys.exit(1)

    # Call function to convert audio to nus3bank
    convert_audio_to_nus3bank(args.input_audio, args.audio_type, args.game, args.preview_point, args.song_id)

if __name__ == "__main__":
    main()
