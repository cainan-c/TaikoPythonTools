import os
import sys
from pydub import AudioSegment

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

if __name__ == "__main__":
    # Check command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python audio_converter.py <input_file> <output_file>")
        sys.exit(1)

    input_audio_file = sys.argv[1]
    output_audio_file = sys.argv[2]

    try:
        convert_audio_to_wav(input_audio_file, output_audio_file)
        print(f"Conversion successful. Output file: {output_audio_file}")
    except Exception as e:
        print(f"Error during conversion: {e}")
