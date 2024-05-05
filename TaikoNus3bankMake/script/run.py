import os
import sys
import subprocess

def run_script(script_name, script_args):
    script_path = os.path.join('script', script_name, f'{script_name}.py')
    if os.path.exists(script_path):
        command = ['python', script_path] + script_args
        subprocess.run(command)
    else:
        print(f"Script '{script_name}' not found.")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python launcher.py <script_name> [<script_args>]")
        sys.exit(1)

    script_name = sys.argv[1]
    script_args = sys.argv[2:]  # Capture all arguments after script_name

    run_script(script_name, script_args)
