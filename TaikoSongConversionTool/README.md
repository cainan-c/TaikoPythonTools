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
Song Data properly converted to the format this tool expects, stored in a folder called `data`.  

Due to copyright reasons, etc. no song data will be provided with this tool, however you can use [TjaBatchConvert](https://github.com/cainan-c/TaikoPythonTools/tree/main/TjaBatchConvert)  to convert custom charts to a format this tool expects.  

Currently, due to the nature of this relying on some Windows executables, this tool currently only supports Windows. 
I will be looking into getting it running on Unix-based operating systems. (Linux/macOS)  

![song conversion tool](https://i.imgur.com/TnRlAxR.png)  

## Tools Used
at9tool - Used to convert audio to the Sony AT9 format.  
[VGAudioCli](https://github.com/Thealexbarney/VGAudio) - Used to convert audio to Nintendo IDSP and Nintendo OPUS.   
[G.722.1 Reference Tool](https://www.itu.int/rec/T-REC-G.722.1-200505-I/en) - Used to convert audio to Polycom Siren 14   

### Special Thanks
Steam User [descatal](https://steamcommunity.com/id/descatal) for writing [this](https://exvsfbce.home.blog/2020/02/04/guide-to-encoding-bnsf-is14-audio-files-converting-wav-back-to-bnsf-is14/) guide on how to create/encode `bnsf` files.   
[korenkonder](https://github.com/korenkonder) for compiling the G.722.1 tool used in this project.  
[Kamui/despairoharmony](https://github.com/despairoharmony) for some of the Nijiiro `.nus3bank` template research.  

## Related Tools
[tja2fumen](https://github.com/vivaria/tja2fumen)  
[TjaOffsetNeutralise](https://github.com/cainan-c/TaikoPythonTools/tree/main/TjaOffsetNeutralise)  
[TjaBatchConvert](https://github.com/cainan-c/TaikoPythonTools/tree/main/TjaBatchConvert)  