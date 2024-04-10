import subprocess

def run_script(script_name):
    try:
        subprocess.run(["python", script_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        raise

if __name__ == "__main__":
    try:
        # Run musicinfo_merge.py
        print("Merging musicinfo entries...")
        run_script("musicinfo_merge.py")

        # Run wordlist_merge.py
        print("Merging wordlist entries...")
        run_script("wordlist_merge.py")

        # Run copy.py
        print("Copying audio to the specified output folder...")
        run_script("copy.py")

        # Run encrypt.py
        print("Encrypting and copying merged datatable files...")
        run_script("encrypt.py")

        # All scripts executed successfully
        print("Missing songs successfully added.\nPress Enter to Exit")

    except Exception as e:
        print(f"Error: {e}")

    input()  # Wait for user to press Enter before exiting
