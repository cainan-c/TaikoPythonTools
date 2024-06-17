import re
import os
import shutil
from pydub import AudioSegment

def process_tja_and_audio(tja_path, output_dir=None, original_name=False):
    # Read the TJA file contents
    with open(tja_path, 'r', encoding='shift_jis') as file:
        tja_contents = file.read()

    # Extract BPM, OFFSET, and WAVE
    bpm_match = re.search(r'BPM:([\d.]+)', tja_contents)
    offset_match = re.search(r'OFFSET:([-?\d.]+)', tja_contents)
    wave_match = re.search(r'WAVE:(.+)', tja_contents)

    if bpm_match and offset_match and wave_match:
        bpm = float(bpm_match.group(1))
        offset = float(offset_match.group(1))
        wave = wave_match.group(1).strip()

        # Calculate the duration of one measure in milliseconds
        one_measure_ms = (60000 / bpm) * 4  # 4 beats per measure in common time

        # Resolve the path to the .ogg audio file
        wave_file = os.path.basename(wave)
        wave_path = os.path.join(os.path.dirname(tja_path), wave_file)
        if not os.path.isfile(wave_path):
            print(f"Audio file {wave_path} not found.")
            return

        # Load the .ogg audio file
        audio = AudioSegment.from_file(wave_path)

        # Add the delay for one measure
        adjusted_audio = AudioSegment.silent(duration=one_measure_ms) + audio

        # Calculate the offset in milliseconds
        offset_ms = offset * 1000

        # Apply the offset (add or subtract silence at the beginning)
        if offset_ms > 0:
            adjusted_audio = AudioSegment.silent(duration=offset_ms) + adjusted_audio
        else:
            adjusted_audio = adjusted_audio[-offset_ms:] if len(adjusted_audio) > -offset_ms else adjusted_audio

        # Determine output file paths
        base_name = os.path.basename(tja_path).replace('.tja', '')
        if output_dir:
            if original_name:
                adjusted_audio_path = os.path.join(output_dir, f'{base_name}.ogg')
                new_tja_path = os.path.join(output_dir, f'{base_name}.tja')
            else:
                adjusted_audio_path = os.path.join(output_dir, f'{base_name}_adjusted.ogg')
                new_tja_path = os.path.join(output_dir, f'{base_name}_modified.tja')
        else:
            if original_name:
                adjusted_audio_path = tja_path.replace('.tja', '_adjusted.ogg')
                new_tja_path = tja_path.replace('.tja', '_modified.tja')
            else:
                adjusted_audio_path = tja_path.replace('.tja', '_adjusted.ogg')
                new_tja_path = tja_path.replace('.tja', '_modified.tja')

        # Save the adjusted audio to a new file
        adjusted_audio.export(adjusted_audio_path, format='ogg')

        # Prepare the new content for the TJA file
        new_content = ''
        for line in tja_contents.splitlines():
            if line.startswith('OFFSET'):
                new_content += 'OFFSET:0\n'
            elif line.startswith('WAVE'):
                new_content += f'WAVE:{wave_file}\n'
            else:
                new_content += line + '\n'
            if line.strip() == '#START':
                new_content += ',' + '\n'

        # Save the modified TJA content to a new file
        with open(new_tja_path, 'w', encoding='shift_jis') as new_file:
            new_file.write(new_content)

        print(f"One measure duration (ms): {one_measure_ms}")
        print(f"Calculated delay (ms): {one_measure_ms}")
        print(f"Applied offset (ms): {offset_ms}")
        print(f"Adjusted audio saved to: {adjusted_audio_path}")
        print(f"Modified TJA content saved to: {new_tja_path}")
    else:
        print("BPM, OFFSET, or WAVE not found in the TJA file.")

def process_directory(input_dir, output_dir):
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.tja'):
                tja_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, input_dir)
                output_subdir = os.path.join(output_dir, relative_path)
                os.makedirs(output_subdir, exist_ok=True)
                process_tja_and_audio(tja_path, output_subdir, original_name=True)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Process TJA and OGG files.')
    parser.add_argument('--file', type=str, help='Path to a single TJA file')
    parser.add_argument('--path', type=str, help='Path to a directory containing folders with TJA files')

    args = parser.parse_args()

    if args.file:
        process_tja_and_audio(args.file, original_name=True)
    elif args.path:
        output_dir = args.path + '_adjusted'
        shutil.rmtree(output_dir, ignore_errors=True)  # Remove the output directory if it exists
        os.makedirs(output_dir, exist_ok=True)
        process_directory(args.path, output_dir)
    else:
        print("Please specify either --file or --path.")
