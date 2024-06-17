# TJA Batch Conversion

Python script that converts TJA files and audio for use with [TaikoSongConversionTool](https://github.com/cainan-c/TaikoPythonTools/tree/main/TaikoSongConversionTool)  
The tool isn't very fast, due to the JSON files becoming malformed when multi-threading is involved.  
This tool can convert roughly 28 songs per minute.  

This tool takes advantage of vivaria's [tja2fumen](https://github.com/vivaria/tja2fumen) for conversion.  

Each folder containing `.tja` files must have a `box.def` file.

Prerequisites:
Python 3.12.3 or newer  
pydub installed through pip `pip install pydub`  

Usage: batch_convert.py [-h] input_folder output_folder  

Process TJA files and generate related files.  

positional arguments:  
  input_folder   The input folder containing TJA files.  
  output_folder  The output folder where processed files will be saved.  

options:  
  -h, --help     show this help message and exit  

## Known Issues
Not all charts will properly convert, this is due to limitations within [tja2fumen](https://github.com/vivaria/tja2fumen), please refer to that project's readme for information on what is and isn't supported.
Song titles may not properly display in-game, this is due to not all unicode characters being supported within Taiko no Tatsujin games.
