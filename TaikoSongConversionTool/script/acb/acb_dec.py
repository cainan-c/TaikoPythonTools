import os
import argparse
import subprocess
import shutil
import tempfile
from pydub import AudioSegment

def parse_arguments():
    parser = argparse.ArgumentParser(description='CLI tool to create .acb files')
    parser.add_argument('input_audio', type=str, help='Path to the input audio file')
    parser.add_argument('song_id', type=str, help='Song ID')
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Generate a unique random temporary folder name
    with tempfile.TemporaryDirectory(prefix='song_') as temp_folder:
        try:
            # Convert input audio to 44100Hz WAV
            input_audio = args.input_audio
            temp_wav_file = os.path.join(temp_folder, f'input_{args.song_id}.wav')

            audio = AudioSegment.from_file(input_audio)
            audio = audio.set_frame_rate(44100)
            audio.export(temp_wav_file, format='wav')

            # Generate .hca file using VGAudioCli.exe
            hca_folder = os.path.join(temp_folder, f'song_{args.song_id}')
            os.makedirs(hca_folder, exist_ok=True)
            hca_file = os.path.join(hca_folder, '00000.hca')
            subprocess.run(['bin/VGAudioCli.exe', temp_wav_file, hca_file], check=True)

            # Copy sample .acb template to temporary location
            acb_template = 'templates/song_sample.acb'
            temp_acb_file = os.path.join(temp_folder, f'song_{args.song_id}.acb')
            shutil.copy(acb_template, temp_acb_file)

            # Edit .acb using ACBEditor
            subprocess.run(['bin/ACBEditor.exe', hca_folder], check=True)

            # Move .acb file to the current directory
            final_acb_file = f'song_{args.song_id}.acb'
            os.replace(temp_acb_file, final_acb_file)

        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()
