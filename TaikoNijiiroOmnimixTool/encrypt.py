import os
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

def encrypt_file(input_file, output_folder, key, iv):
    # Compress the input file
    compressed_file = compress_file(input_file)

    # Read the compressed file
    with open(compressed_file, 'rb') as f_in:
        plaintext = f_in.read()

    # Encrypt the file
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

    # Generate the output filename
    output_filename = os.path.splitext(os.path.basename(compressed_file))[0] + ".bin"

    # Save the encrypted data to the output folder
    output_path = os.path.join(output_folder, output_filename)
    with open(output_path, 'wb') as f_out:
        f_out.write(iv + ciphertext)

    print(f"Encryption successful. Encrypted file saved as: {output_path}")

    # Remove the compressed file
    os.remove(compressed_file)
    print(f"Removed the compressed file: {compressed_file}")

def main():
    # Load configuration from config.toml
    config_file = "config.toml"
    with open(config_file, "r") as file:
        config = toml.load(file)

    # Get key and IV from configuration and convert them to bytes
    key_hex = config["key"]["key"]
    key = bytes.fromhex(key_hex)
    iv = bytes.fromhex("FF" * 16)  # IV set to FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF

    # Get the input folder and output folder from the configuration
    input_folder = "datatable_merged"
    output_folder = config["output"]["folder"]
    datatable_folder = os.path.join(output_folder, "datatable")

    # Create the datatable folder if it doesn't exist
    os.makedirs(datatable_folder, exist_ok=True)

    # Process each JSON file in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            input_file = os.path.join(input_folder, filename)

            # Encrypt the JSON file and save the encrypted file to the datatable folder
            encrypt_file(input_file, datatable_folder, key, iv)

if __name__ == "__main__":
    main()
