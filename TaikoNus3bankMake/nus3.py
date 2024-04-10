import sys
import os
import struct
import random
import toml

def generate_random_uint16_hex():
    return format(random.randint(0, 65535), '04X')

def load_template_config():
    # Load template configurations from config.toml (if needed in the future)
    # This function can be expanded to load more template configurations if necessary
    # For now, we don't need to use this function directly for selecting templates
    return {}

def select_template_name(output_file):
    # Determine the appropriate template name based on the length of the output file name
    base_filename = os.path.splitext(output_file)[0]
    length = len(base_filename)

    if length == 8:
        return "song_ABC"
    elif length == 9:
        return "song_ABCD"
    elif length == 10:
        return "song_ABCDE"
    elif length == 11:
        return "song_ABCDEF"
    else:
        raise ValueError("Output file name length (excluding extension) must be between 8 and 12 characters.")

def modify_nus3bank_template(template_name, audio_file, preview_point, output_file):
    # Define template configurations based on the selected template_name
    template_configs = {
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
        }
    }

    # Retrieve template configurations for the specified template_name
    template_config = template_configs[template_name]

    # Read template nus3bank file from the templates folder
    template_file = os.path.join("templates", template_config['template_file'])
    with open(template_file, 'rb') as f:
        template_data = bytearray(f.read())

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

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: audio.py <audio_file> <preview_point> <output_file>")
        sys.exit(1)

    audio_file = sys.argv[1]
    preview_point = sys.argv[2]
    output_file = sys.argv[3]

    try:
        template_name = select_template_name(output_file)
        modify_nus3bank_template(template_name, audio_file, preview_point, output_file)
        print(f"Created {output_file} successfully.")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
