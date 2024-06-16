import sys
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

KEY = bytes.fromhex("54704643596B474170554B6D487A597A")
IV = bytes.fromhex("FF" * 16)  # IV for encryption

def encrypt_file(input_filename, output_filename):
    with open(input_filename, 'rb') as infile:
        plaintext = infile.read()

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plaintext) + padder.finalize()

    cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    with open(output_filename, 'wb') as outfile:
        outfile.write(IV + ciphertext)

def decrypt_file(input_filename, output_filename):
    with open(input_filename, 'rb') as infile:
        encrypted_data = infile.read()

    iv = encrypted_data[:16]  # Extract IV from the beginning of the file

    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data[16:]) + decryptor.finalize()

    # Print the decrypted data (for debugging purposes)
    #print("Decrypted data (hex):", decrypted_data.hex())

    with open(output_filename, 'wb') as outfile:
        outfile.write(decrypted_data)
        
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python file_encrypt_decrypt.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if os.path.exists(input_file):
        if input_file != output_file:
            if input("Encrypt (e) or Decrypt (d) the file? ").lower() == 'e':
                encrypt_file(input_file, output_file)
                print("Encryption complete.")
            else:
                decrypt_file(input_file, output_file)
                print("Decryption complete.")
        else:
            print("Error: Output file must be different from input file.")
    else:
        print(f"Error: Input file '{input_file}' not found.")
