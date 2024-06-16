import subprocess
import os
import sys
import shutil
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

def convert_to_mono_48k(input_file, output_file):
    """Convert input audio file to 16-bit mono WAV with 48000 Hz sample rate."""
    try:
        audio = AudioSegment.from_file(input_file)
        audio = audio.set_channels(1)  # Convert to mono
        audio = audio.set_frame_rate(48000)  # Set frame rate to 48000 Hz
        audio = audio.set_sample_width(2)  # Set sample width to 16-bit (2 bytes)
        audio.export(output_file, format='wav')
    except CouldntDecodeError:
        print(f"Error: Unable to decode {input_file}. Please provide a valid audio file.")
        sys.exit(1)


def run_encode_tool(input_wav, output_bs):
    """Run external encode tool with specified arguments."""
    subprocess.run(['bin/encode.exe', '0', input_wav, output_bs, '48000', '14000'])


def modify_bnsf_template(output_bs, output_bnsf, header_size, total_samples):
    """Modify the BNSF template file with calculated values and combine with output.bs."""
    # Calculate the file size of output.bs
    bs_file_size = os.path.getsize(output_bs)

    # Create modified BNSF data
    new_file_size = bs_file_size + header_size - 0x8
    total_samples_bytes = total_samples.to_bytes(4, 'big')
    bs_file_size_bytes = bs_file_size.to_bytes(4, 'big')
    
    # Read BNSF template data
    with open('bin/header.bnsf', 'rb') as template_file:
        bnsf_template_data = bytearray(template_file.read())

    # Modify BNSF template with calculated values
    bnsf_template_data[0x4:0x8] = new_file_size.to_bytes(4, 'big')  # File size
    bnsf_template_data[0x1C:0x20] = total_samples_bytes  # Total sample count
    bnsf_template_data[0x2C:0x30] = bs_file_size_bytes  # Size of output.bs

    # Append output.bs data to modified BNSF template
    with open(output_bs, 'rb') as bs_file:
        bs_data = bs_file.read()
        final_bnsf_data = bnsf_template_data + bs_data

    # Write final BNSF file
    with open(output_bnsf, 'wb') as output_file:
        output_file.write(final_bnsf_data)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python bnsf.py <input_audio> [<output_bnsf>]")
        sys.exit(1)

    input_audio = sys.argv[1]
    output_bnsf = sys.argv[2] if len(sys.argv) > 2 else 'output.bnsf'

    # Create temp folder if it doesn't exist
    temp_folder = 'temp'
    os.makedirs(temp_folder, exist_ok=True)

    # Temporary file paths
    output_wav = os.path.join(temp_folder, 'output_mono.wav')
    output_bs = os.path.join(temp_folder, 'output.bs')

    # Header size (assuming fixed size)
    header_size = 0x30

    try:
        # Step 1: Convert input audio to required format (WAV)
        convert_to_mono_48k(input_audio, output_wav)

        # Step 2: Run external encoding tool
        run_encode_tool(output_wav, output_bs)

        # Step 3: Get sample count from the converted mono WAV
        mono_wav = AudioSegment.from_wav(output_wav)
        total_samples = len(mono_wav.get_array_of_samples())

        # Step 4: Modify BNSF template with calculated values and combine with output.bs
        modify_bnsf_template(output_bs, output_bnsf, header_size, total_samples)

        print("BNSF file created:", output_bnsf)

    finally:
        # Cleanup: Delete temporary files and temp folder
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
