# Very simple python script that replaces the timing values in a Fumen and spits out a new file.

import sys

# Define's possible file name difficulties.
easy = '_e'
normal = '_n'
# Below isn't actually used, could be but not needed.
hard = '_h'
extreme = '_m'
ura = '_x'

# Open Easy/Normal's timing file
with open('timing_easy.bin', 'rb') as timing_binary_easy:
    timing_window_easy = timing_binary_easy.read()

# Open Hard/Extreme/Ura's timing file    
with open('timing_hard.bin', 'rb') as timing_binary_hard:
    timing_window_hard = timing_binary_hard.read()    

# Very shit check to see if anything (other than the python file) has been entered.
# If two files aren't entered, it'll just thow a normal Python error.
if len(sys.argv) > 1:
    # Define the input and output files.
    inFile = sys.argv[1]
    outFile = sys.argv[2]

    # Opens the input file, saves it as the output,
    # This was the only way I managed was able to acomplish the right output.
    with open(inFile, "rb") as old, open(outFile, "wb") as new:
        old.seek(0)
        new.write(old.read())
    
    # Actually replaces the timing windows
    chart_new = open(outFile, "rb+")
    chart_new.seek(0)
    
    # Checks if _e, _n, etc is present in the file name:
    # If it is, it'll use timing_easy,
    # If it isn't present, it will use timing_hard instead.
    if easy in inFile:
        chart_new.write(timing_window_easy)
        chart_new.close()
    elif normal in inFile:
        chart_new.write(timing_window_easy)
        chart_new.close()
    else:
        chart_new.write(timing_window_hard)
        chart_new.close()
    
else:
    print("Usage:",sys.argv[0], "inFile outFile",
    "\n\nEasy and Normal charts use timing_easy.bin"
    "\nHard, Extreme and Ura use timing_hard.bin"
    "\n\nDifficulty Detection is based on the input's File name.")