import os
import sys
import toml
import gzip
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def decrypt_and_rename_to_gz(input_file, key):
    # Read the encrypted file
    with open(input_file, 'rb') as file:
        encrypted_bytes = file.read()

    # Extract IV from the first 16 bytes of the encrypted file
    iv = encrypted_bytes[:16]

    # Decrypt the rest of the file
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes[16:]), AES.block_size)

    # Generate the new filename with .gz extension
    output_file = os.path.splitext(input_file)[0] + ".gz"
    
    # Write decrypted data to the new .gz file
    with open(output_file, 'wb') as file:
        file.write(decrypted_bytes)

    print(f"Decryption successful. Renamed and decrypted file saved as: {output_file}")

    return output_file

def decompress_gz_file(input_file):
    # Generate the output filename without the .gz extension
    output_file = os.path.splitext(input_file)[0]

    # Decompress the .gz file
    with gzip.open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
        f_out.write(f_in.read())

    print(f"Decompression successful. Decompressed file saved as: {output_file}")

    return output_file

def move_to_decrypted_folder(input_file, output_file):
    # Create the decrypted folder if it doesn't exist
    decrypted_folder = os.path.join(os.path.dirname(input_file), "decrypted")
    os.makedirs(decrypted_folder, exist_ok=True)

    # Generate the output filename within the decrypted folder with .bin extension
    output_bin_file = os.path.join(decrypted_folder, os.path.splitext(os.path.basename(output_file))[0] + ".bin")

    # Move the decrypted and decompressed file to the decrypted folder
    os.rename(output_file, output_bin_file)

    print(f"Decrypted file moved to folder 'decrypted'. Decrypted file saved as: {output_bin_file}")

def main():
    # Check if there are any files dragged and dropped
    if len(sys.argv) < 2:
        print("Please drag and drop the AES-256-CBC encrypted .bin file(s) onto this program.")
        return

    # Load configuration from config.toml
    config_file = "config.toml"
    with open(config_file, "r") as file:
        config = toml.load(file)

    # Get key from configuration and convert it to bytes
    key_hex = config["key"]
    key = bytes.fromhex(key_hex)

    for input_file in sys.argv[1:]:
        # Decrypt the file and get the renamed .gz file
        gz_file = decrypt_and_rename_to_gz(input_file, key)

        # Decompress the .gz file and get the output filename
        output_file = decompress_gz_file(gz_file)

        # Move the decrypted and decompressed file to the decrypted folder
        move_to_decrypted_folder(input_file, output_file)

        # Remove the .gz file
        os.remove(gz_file)
        print(f"Removed the .gz file: {gz_file}")

if __name__ == "__main__":
    main()
