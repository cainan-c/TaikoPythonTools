# TJA Batch Conversion

Python script that converts TJA files and audio for use with [TaikoSongConversionTool](https://github.com/cainan-c/TaikoPythonTools/tree/main/TaikoSongConversionTool)  
The tool isn't very fast, due to the JSON files becoming malformed when multi-threading is involved.  

This tool takes advantage of vivaria's [tja2fumen](https://github.com/vivaria/tja2fumen) for conversion.  

Usage: batch_convert.py [-h] input_folder output_folder  

Process TJA files and generate related files.  

positional arguments:  
  input_folder   The input folder containing TJA files.  
  output_folder  The output folder where processed files will be saved.  

options:  
  -h, --help     show this help message and exit  
