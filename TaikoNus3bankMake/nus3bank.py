import argparse
import subprocess
import os
import sys
import shutil
import tempfile
import random
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

#from idsp.py
def convert_audio_to_idsp(input_file, output_file):
    temp_folder = tempfile.mkdtemp()
    try:
        if not input_file.lower().endswith('.wav'):
            temp_wav_file = os.path.join(temp_folder, "temp.wav")
            audio = AudioSegment.from_file(input_file)
            audio.export(temp_wav_file, format="wav")
            input_file = temp_wav_file

        vgaudio_cli_path = os.path.join("bin", "VGAudioCli.exe")
        subprocess.run([vgaudio_cli_path, "-i", input_file, "-o", output_file], check=True)
    finally:
        shutil.rmtree(temp_folder, ignore_errors=True)

#from lopus.py
def convert_audio_to_opus(input_file, output_file):
    # Create a unique temporary folder to store intermediate files
    temp_folder = tempfile.mkdtemp()

    try:
        # Check if the input file is already in WAV format
        if not input_file.lower().endswith('.wav'):
            # Load the input audio file using pydub and convert to WAV
            temp_wav_file = os.path.join(temp_folder, "temp.wav")
            audio = AudioSegment.from_file(input_file)
            audio = audio.set_frame_rate(48000)  # Set frame rate to 48000 Hz
            audio.export(temp_wav_file, format="wav")
            input_file = temp_wav_file

        # Path to VGAudioCli executable
        vgaudio_cli_path = os.path.join("bin", "VGAudioCli.exe")

        # Run VGAudioCli to convert WAV to Switch OPUS
        subprocess.run([vgaudio_cli_path, "-i", input_file, "-o", output_file, "--opusheader", "namco"], check=True)

    finally:
        # Clean up temporary folder
        shutil.rmtree(temp_folder, ignore_errors=True)

#from wav.py
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

#from at9.py
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

# from bnsf.py
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
    with open('templates/header.bnsf', 'rb') as template_file:
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

#from nus3.py
def generate_random_uint16_hex():
    return format(random.randint(0, 65535), '04X')

def select_template_name(game, output_file):
    base_filename = os.path.splitext(output_file)[0]
    length = len(base_filename)

    if game == "nijiiro":
        if length == 8:
            return "song_ABC"
        elif length == 9:
            return "song_ABCD"
        elif length == 10:
            return "song_ABCDE"
        elif length == 11:
            return "song_ABCDEF"
        elif length == 12:
            return "song_ABCDEFG"    
        elif length == 13:
            return "song_ABCDEFGH"
    elif game == "ps4":
        if length == 8:
            return "song_ABC"
        elif length == 9:
            return "song_ABCD"
        elif length == 10:
            return "song_ABCDE"
        elif length == 11:
            return "song_ABCDEF"
    elif game == "ns1":
        if length == 8:
            return "song_ABC"
        elif length == 9:
            return "song_ABCD"
        elif length == 10:
            return "song_ABCDE"
        elif length == 11:
            return "song_ABCDEF"
    elif game == "wiiu3":
        if length == 8:
            return "song_ABC"
        elif length == 9:
            return "song_ABCD"
        elif length == 10:
            return "song_ABCDE"
        elif length == 11:
            return "song_ABCDEF"

    raise ValueError("Unsupported game or output file name length.")

def modify_nus3bank_template(game, template_name, audio_file, preview_point, output_file):
    game_templates = {        
        "nijiiro": {
            "template_folder": "nijiiro",
            "templates": {
                "song_ABC": {
                    "unique_id_offset": 176,
                    "audio_size_offsets": [76, 1568, 1852],
                    "preview_point_offset": 1724,
                    "song_placeholder": "song_ABC",
                    "template_file": "song_ABC.nus3bank"
                },
                "song_ABCD": {
                    "unique_id_offset": 176,
                    "audio_size_offsets": [76, 1568, 1852],
                    "preview_point_offset": 1724,
                    "song_placeholder": "song_ABCD",
                    "template_file": "song_ABCD.nus3bank"
                },
                "song_ABCDE": {
                    "unique_id_offset": 176,
                    "audio_size_offsets": [76, 1568, 1852],
                    "preview_point_offset": 1724,
                    "song_placeholder": "song_ABCDE",
                    "template_file": "song_ABCDE.nus3bank"
                },
                "song_ABCDEF": {
                    "unique_id_offset": 180,
                    "audio_size_offsets": [76, 1576, 1868],
                    "preview_point_offset": 1732,
                    "song_placeholder": "song_ABCDEF",
                    "template_file": "song_ABCDEF.nus3bank"
                },
                "song_ABCDEFG": {
                    "unique_id_offset": 180,
                    "audio_size_offsets": [76, 1672, 1964],
                    "preview_point_offset": 1824,
                    "song_placeholder": "song_ABCDEFG",
                    "template_file": "song_ABCDEFG.nus3bank"
                },
                "song_ABCDEFGH": {
                    "unique_id_offset": 180,
                    "audio_size_offsets": [76, 1576, 1868],
                    "preview_point_offset": 1732,
                    "song_placeholder": "song_ABCDEFGH",
                    "template_file": "song_ABCDEFGH.nus3bank"
                },            
            }
        },
        "ns1": {
            "template_folder": "ns1",
            "templates": {
                "song_ABC": {
                    "audio_size_offsets": [76, 5200, 5420],
                    "preview_point_offset": 5324,
                    "song_placeholder": "SONG_ABC",
                    "template_file": "SONG_ABC.nus3bank"
                },
                "song_ABCD": {
                    "audio_size_offsets": [76, 5200, 5420],
                    "preview_point_offset": 5324,
                    "song_placeholder": "SONG_ABCD",
                    "template_file": "SONG_ABCD.nus3bank"
                },
                "song_ABCDE": {
                    "audio_size_offsets": [76, 5200, 5404],
                    "preview_point_offset": 5320,
                    "song_placeholder": "SONG_ABCDE",
                    "template_file": "SONG_ABCDE.nus3bank"
                },
                "song_ABCDEF": {
                    "audio_size_offsets": [76, 5208, 5420],
                    "preview_point_offset": 5324,
                    "song_placeholder": "SONG_ABCDEF",
                    "template_file": "SONG_ABCDEF.nus3bank"
                }
            }
        },
        "ps4": {
            "template_folder": "ps4",
            "templates": {
                "song_ABC": {
                    "audio_size_offsets": [76, 3220, 3436],
                    "preview_point_offset": 3344,
                    "song_placeholder": "SONG_ABC",
                    "template_file": "SONG_ABC.nus3bank"
                },
                "song_ABCD": {
                    "audio_size_offsets": [76, 3220, 3436],
                    "preview_point_offset": 3344,
                    "song_placeholder": "SONG_ABCD",
                    "template_file": "SONG_ABCD.nus3bank"
                },
                "song_ABCDE": {
                    "audio_size_offsets": [76, 3220, 3436],
                    "preview_point_offset": 3344,
                    "song_placeholder": "SONG_ABCDE",
                    "template_file": "SONG_ABCDE.nus3bank"
                },
                "song_ABCDEF": {
                    "audio_size_offsets": [76, 3228, 3452],
                    "preview_point_offset": 3352,
                    "song_placeholder": "SONG_ABCDEF",
                    "template_file": "SONG_ABCDEF.nus3bank"
                }
            }
        },
        "wiiu3": {
            "template_folder": "wiiu3",
            "templates": {
                "song_ABC": {
                    "audio_size_offsets": [76, 3420, 3612],
                    "preview_point_offset": 3540,
                    "song_placeholder": "SONG_ABC",
                    "template_file": "SONG_ABC.nus3bank"
                },
                "song_ABCD": {
                    "audio_size_offsets": [76, 3420, 3612],
                    "preview_point_offset": 3540,
                    "song_placeholder": "SONG_ABCD",
                    "template_file": "SONG_ABCD.nus3bank"
                },
                "song_ABCDE": {
                    "audio_size_offsets": [76, 3420, 3612],
                    "preview_point_offset": 3540,
                    "song_placeholder": "SONG_ABCDE",
                    "template_file": "SONG_ABCDE.nus3bank"
                },
                "song_ABCDEF": {
                    "audio_size_offsets": [76, 3428, 3612],
                    "preview_point_offset": 3548,
                    "song_placeholder": "SONG_ABCDEF",
                    "template_file": "SONG_ABCDEF.nus3bank"
                }
            }
        },
    }

    if game not in game_templates:
        raise ValueError("Unsupported game.")

    templates_config = game_templates[game]

    if template_name not in templates_config["templates"]:
        raise ValueError(f"Unsupported template for {game}.")

    template_config = templates_config["templates"][template_name]
    template_folder = templates_config["template_folder"]

    # Read template nus3bank file from the specified game's template folder
    template_file = os.path.join("templates", template_folder, template_config['template_file'])
    with open(template_file, 'rb') as f:
        template_data = bytearray(f.read())

    # Set unique ID if it exists in the template configuration
    if 'unique_id_offset' in template_config:
        # Generate random UInt16 hex for unique ID
        unique_id_hex = generate_random_uint16_hex()
        # Set unique ID in the template data at the specified offset
        template_data[template_config['unique_id_offset']:template_config['unique_id_offset']+2] = bytes.fromhex(unique_id_hex)

    # Get size of the audio file in bytes
    audio_size = os.path.getsize(audio_file)

    # Convert audio size to UInt32 bytes in little-endian format
    size_bytes = audio_size.to_bytes(4, 'little')

    # Set audio size in the template data at the specified offsets
    for offset in template_config['audio_size_offsets']:
        template_data[offset:offset+4] = size_bytes

    # Convert preview point (milliseconds) to UInt32 bytes in little-endian format
    preview_point_ms = int(preview_point)
    preview_point_bytes = preview_point_ms.to_bytes(4, 'little')

    # Set preview point in the template data at the specified offset
    template_data[template_config['preview_point_offset']:template_config['preview_point_offset']+4] = preview_point_bytes

    # Replace song name placeholder with the output file name in bytes
    output_file_bytes = output_file.encode('utf-8')
    template_data = template_data.replace(template_config['song_placeholder'].encode('utf-8'), output_file_bytes.replace(b'.nus3bank', b''))

    # Append the audio file contents to the modified template data
    with open(audio_file, 'rb') as audio:
        template_data += audio.read()

    # Write the modified data to the output file
    with open(output_file, 'wb') as out:
        out.write(template_data)

    print(f"Created {output_file} successfully.")

# from script.py
def run_script(script_name, script_args):
    if script_name == "idsp":
        input_file, output_file = script_args
        convert_audio_to_idsp(input_file, output_file)
    elif script_name == "lopus":
        input_file, output_file = script_args
        convert_audio_to_opus(input_file, output_file)
    elif script_name == "at9":
        input_file, output_file = script_args
        convert_audio_to_at9(input_file, output_file)        
    elif script_name == "wav":
        input_file, output_file = script_args
        convert_audio_to_wav(input_file, output_file)              
    elif script_name == "bnsf":
        input_audio, output_bnsf = script_args
        temp_folder = 'temp'
        os.makedirs(temp_folder, exist_ok=True)
        output_wav = os.path.join(temp_folder, 'output_mono.wav')
        output_bs = os.path.join(temp_folder, 'output.bs')
        header_size = 0x30
        
        try:
            convert_to_mono_48k(input_audio, output_wav)
            run_encode_tool(output_wav, output_bs)
            mono_wav = AudioSegment.from_wav(output_wav)
            total_samples = len(mono_wav.get_array_of_samples())
            modify_bnsf_template(output_bs, output_bnsf, header_size, total_samples)
            print("BNSF file created:", output_bnsf)
        finally:
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder)    
    elif script_name == "nus3":
        game, audio_file, preview_point, output_file = script_args
        template_name = select_template_name(game, output_file)
        modify_nus3bank_template(game, template_name, audio_file, preview_point, output_file)
    else:
        print(f"Unsupported script: {script_name}")
        sys.exit(1)

#from conv.py
def convert_audio_to_nus3bank(input_audio, audio_type, game, preview_point, song_id):
    output_filename = f"song_{song_id}.nus3bank"
    converted_audio_file = f"{input_audio}.{audio_type}"

    if audio_type in ["bnsf", "at9", "idsp", "lopus", "wav"]:
        conversion_command = ["python", __file__, audio_type, input_audio, converted_audio_file]
        nus3_command = ["python", __file__, "nus3", game, converted_audio_file, str(preview_point), output_filename]

        try:
            subprocess.run(conversion_command, check=True)
            subprocess.run(nus3_command, check=True)
            print(f"Conversion successful! Created {output_filename}")

            if os.path.exists(converted_audio_file):
                os.remove(converted_audio_file)
                print(f"Deleted {converted_audio_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
    else:
        print(f"Unsupported audio type: {audio_type}")

def main():
    parser = argparse.ArgumentParser(description="Convert audio to nus3bank")
    parser.add_argument("input_audio", type=str, nargs="?", help="Input audio file path.")
    parser.add_argument("audio_type", type=str, nargs="?", help="Type of input audio (e.g., wav, bnsf, at9, idsp, lopus).")
    parser.add_argument("game", type=str, nargs="?", help="Game type (e.g., nijiiro, ns1, ps4, wiiu3).")
    parser.add_argument("preview_point", type=int, nargs="?", help="Audio preview point in ms.")
    parser.add_argument("song_id", type=str, nargs="?", help="Song ID for the nus3bank file.")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    if not args.input_audio:
        print("Error: Input audio file path is required.")
        parser.print_help()
        sys.exit(1)

    if args.audio_type in ["bnsf", "at9", "idsp", "lopus", "wav"] and args.game and args.preview_point and args.song_id:
        convert_audio_to_nus3bank(args.input_audio, args.audio_type, args.game, args.preview_point, args.song_id)
    else:
        script_name = sys.argv[1]
        script_args = sys.argv[2:]
        run_script(script_name, script_args)

if __name__ == "__main__":
    main()
