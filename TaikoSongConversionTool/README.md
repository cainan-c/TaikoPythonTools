# Taiko no Tatsujin - Song Conversion Tool 

Python based tool that can convert official songs over to some Taiko no Tatsujin games.  

Supported Titles:  
Nintendo Switch Version / Drum 'n' Fun v1.4.13 (Nintendo Switch)  
Drum Session (Any Update) (PlayStation 4)  
Pop Tap Beat (Any Update) (iOS/MacOS/Apple TV)  

A version of this tool with all song data can be found elsewhere.
There's 3 options to sort songs by: ID (A-Z), Song Name (A-Z) and Genre  

This is still a work in-progress, so please report any issues found to me, along with suggestions for features or game support.  

Prerequisites:  
Python 3.12.3 or newer  
tkinter installed through pip `pip install tk`  
cryptography installed through pip `pip install cryptography`  
pydub installed through pip `pip install pydub`  
ffplay installed in `path`.  
Game Data properly converted to the format this tool expects, stored in a folder called `data`.  

Due to copyright reasons, etc. no song data will be provided with this tool, however template data can be found within the `data` folder, which should give an idea of what the tool requires.    

Currently, due to the nature of this relying on some Windows executables, this tool currently only supports Windows. 
I will be looking into getting it running on Unix-based operating systems. (Linux/macOS)  

![song conversion tool](https://i.imgur.com/TnRlAxR.png)  
