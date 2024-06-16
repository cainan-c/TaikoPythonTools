import os
import argparse
import subprocess
import shutil
import tempfile
from pydub import AudioSegment
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def parse_arguments():
    parser = argparse.ArgumentParser(description='CLI tool to create .acb files and encrypt them')
    parser.add_argument('input_audio', type=str, help='Path to the input audio file')
    parser.add_argument('song_id', type=str, help='Song ID')
    return parser.parse_args()

def encrypt_file(input_file, output_file, key, iv):
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

            # Encrypt .acb file to .bin with IV prepended
            key = bytes.fromhex('54704643596B474170554B6D487A597A')
            iv = bytes([0xFF] * 16)
            encrypted_bin_file = os.path.join(temp_folder, f'song_{args.song_id}.bin')
            encrypt_file(temp_acb_file, encrypted_bin_file, key, iv)

            # Move encrypted .bin file to the root folder
            final_bin_file = f'song_{args.song_id}.bin'
            shutil.move(encrypted_bin_file, final_bin_file)

        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()
