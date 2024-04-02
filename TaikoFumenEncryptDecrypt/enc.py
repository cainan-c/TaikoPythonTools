import os
import sys
import toml
import gzip
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

def compress_file(input_file):
    # Generate the output filename with .gz extension
    output_file = os.path.splitext(input_file)[0] + ".gz"

    # Compress the input file
    with open(input_file, 'rb') as f_in, gzip.open(output_file, 'wb') as f_out:
        f_out.write(f_in.read())

    print(f"Compression successful. Compressed file saved as: {output_file}")

    return output_file

def encrypt_file(input_file, key, iv):
    # Read the compressed file
    with open(input_file, 'rb') as file:
        plaintext = file.read()

    # Encrypt the file
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

    # Prepend the IV to the ciphertext
    encrypted_data = iv + ciphertext

    # Generate the output filename
    output_file = os.path.splitext(input_file)[0] + ".encrypted.bin"

    # Write the encrypted data to the output file
    with open(output_file, 'wb') as file:
        file.write(encrypted_data)

    print(f"Encryption successful. Encrypted file saved as: {output_file}")

    return output_file

def move_to_encrypted_folder(input_file, output_file):
    # Create the encrypted folder if it doesn't exist
    encrypted_folder = os.path.join(os.path.dirname(input_file), "encrypted")
    os.makedirs(encrypted_folder, exist_ok=True)

    # Generate the output filename within the encrypted folder
    output_encrypted_file = os.path.join(encrypted_folder, os.path.basename(input_file))

    # Move the encrypted file to the encrypted folder
    os.rename(output_file, output_encrypted_file)

    print(f"Encrypted file moved to folder 'encrypted'. Encrypted file saved as: {output_encrypted_file}")

def main():
    # Check if there are any files dragged and dropped
    if len(sys.argv) < 2:
        print("Please drag and drop the files you want to re-compress and re-encrypt onto this program.")
        return

    # Load configuration from config.toml
    config_file = "config.toml"
    with open(config_file, "r") as file:
        config = toml.load(file)

    # Get key and IV from configuration and convert them to bytes
    key_hex = config["key"]
    key = bytes.fromhex(key_hex)
    iv = bytes.fromhex("FF" * 16)  # IV set to FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF

    for input_file in sys.argv[1:]:
        # Compress the file
        compressed_file = compress_file(input_file)

        # Encrypt the compressed file
        encrypted_file = encrypt_file(compressed_file, key, iv)

        # Move the encrypted file to the encrypted folder
        move_to_encrypted_folder(input_file, encrypted_file)

        # Remove the compressed file
        os.remove(compressed_file)
        print(f"Removed the compressed file: {compressed_file}")

if __name__ == "__main__":
    main()
