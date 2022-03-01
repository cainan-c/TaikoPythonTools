#Python script that replaces the timing values in a Fumen and spits out a new file.

import configparser, struct, sys

#Functions to handle converting a float to a binary array
def float_to_hex(f):
    return hex(struct.unpack('>I', struct.pack('<f', f))[0])

def remove_0x(f):
    return f[2:]

def convert_to_bytearray(f):
    return bytes.fromhex(f)
    
config = configparser.ConfigParser()
config.sections()
config.read('timing.ini')

# Define possible endings of file name and their difficulties.
easy = '_e'
normal = '_n'
hard = '_h'
extreme = '_m'
ura = '_x'

# Check to see if anything (other than the python file) has been entered.
# If two files/the timing window haven't been entered, it'll just throw a normal Python error.
if len(sys.argv) > 1:

    #Check if standard/hitwide/hitnarrow/custom was typed in the console
    if sys.argv[3].lower() == 'standard':
        GOOD = config.getfloat('standard', 'good')
        OK = config.getfloat('standard', 'ok')
        BAD = config.getfloat('standard', 'bad')
        GOOD_EASY = config.getfloat('standard', 'good_easy')
        OK_EASY = config.getfloat('standard', 'ok_easy')
        BAD_EASY = config.getfloat('standard', 'bad_easy')

    else:
        try:
            GOOD = config.getfloat(sys.argv[3].lower, 'good')
            OK = config.getfloat(sys.argv[3].lower, 'ok')
            BAD = config.getfloat(sys.argv[3].lower, 'bad')
            GOOD_EASY = config.getfloat(sys.argv[3].lower, 'good_easy')
            OK_EASY = config.getfloat(sys.argv[3].lower, 'ok_easy')
            BAD_EASY = config.getfloat(sys.argv[3].lower, 'bad_easy')
    
        except:
            print("Invalid Input")
            exit()

    #Convert the hex values to a binary array    
    GOOD_HEX = (float_to_hex(GOOD))
    OK_HEX = (float_to_hex(OK))
    BAD_HEX = (float_to_hex(BAD))

    GOOD_FIXED = (remove_0x(GOOD_HEX))
    OK_FIXED = (remove_0x(OK_HEX))
    BAD_FIXED = (remove_0x(BAD_HEX))

    GOOD_BYTES = (convert_to_bytearray(GOOD_FIXED))
    OK_BYTES = (convert_to_bytearray(OK_FIXED))
    BAD_BYTES = (convert_to_bytearray(BAD_FIXED))

    GOOD_EASY_HEX = (float_to_hex(GOOD_EASY))
    OK_EASY_HEX = (float_to_hex(OK_EASY))
    BAD_EASY_HEX = (float_to_hex(BAD_EASY))

    GOOD_EASY_FIXED = (remove_0x(GOOD_EASY_HEX))
    OK_EASY_FIXED = (remove_0x(OK_EASY_HEX))
    BAD_EASY_FIXED = (remove_0x(BAD_EASY_HEX))

    GOOD_EASY_BYTES = (convert_to_bytearray(GOOD_EASY_FIXED))
    OK_EASY_BYTES = (convert_to_bytearray(OK_EASY_FIXED))
    BAD_EASY_BYTES = (convert_to_bytearray(BAD_EASY_FIXED))

    #Define binary arrays
    timing_window_hard = (GOOD_BYTES + OK_BYTES + BAD_BYTES) * 36
    timing_window_easy = (GOOD_EASY_BYTES + OK_EASY_BYTES + BAD_EASY_BYTES) * 36    


    # Very shit check to see if anything (other than the python file) has been entered.
    # If two files aren't entered, it'll just thow a normal Python error.

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
    print("TaikoFumenTimingReplace\nUsage:",sys.argv[0], "inFile outFile timingWindow",
    "\n\nTiming Options: Standard, Hitnarrow, Hitwide, Custom, Also allows User Defined Values")