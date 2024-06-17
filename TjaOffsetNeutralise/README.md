# TJA Offset Neutraliser 

Incredibly simple script which can take `.tja` files and remove any audio offsets in them. Modifying both the .ogg audio file and the chart iself.   
This tool will add a blank measure to make sure no audio is cut off, etc.  

Recomended to run your TJA files through this tool before using [TjaBatchConvert](https://github.com/cainan-c/TaikoPythonTools/tree/main/TjaBatchConvert)  

Usage: offset_adjust.py [-h] [--file FILE] [--path PATH] [--encoding {shift_jis,utf-8}]  

Process TJA and OGG files.  

options:  
  -h, --help            show this help message and exit  
  --file FILE           Path to a single TJA file  
  --path PATH           Path to a directory containing folders with TJA files  
  --encoding {shift_jis,utf-8}  
                        Encoding type (shift_jis or utf-8)  

