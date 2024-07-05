# Taiko no Tatsujin - Song Conversion Tool 

Python based tool that can convert official songs over to some Taiko no Tatsujin games.  

Current Version: v2a  

### Supported Titles

| Game Title                     | Platform                | Tag                 |Game Version       | Song Limit       |  Supported?      |
| ------------------------------ | ----------------------- | ------------------- | ----------------- | ---------------- | ---------------- |
| Nintendo Switch Version        | Nintendo Switch         | NS1 (JP/ASIA)       | v1.4.13 Only      | 600              | ✅              |
| Drum 'n' Fun                   | Nintendo Switch         | NS1 (EU/USA)        | v1.4.13 Only      | 600              | ✅              |
| Drum Session                   | PlayStation 4           | PS4 (EU/US)         | v1.19 Recommended | 400              | ✅              |
| Drum Session                   | PlayStation 4           | PS4 (JP/ASIA)       | v1.28 Recommended | 400              | ✅              |
| Pop Tap Beat                   | iOS, macOS, Apple TV    | PTB (N/A)           | Any               | 200              | ✅              |
| Atsumete★Tomodachi Daisakusen! | Nintendo Wii U          | WIIU3 (N/A)         | Any               | 90¹              | ✅              |
| Tokumori!                      | Nintendo Wii U          | N/A                 | Any               | Unknown          | ❓ Untested     |
| Wii U Version!                 | Nintendo Wii U          | N/A                 | Any               | Unknown          | ❓ Untested     |

¹Song Limit due to texture limitations, Songs that have URA charts take up 2 slots.    

### Unsupported Titles

| Game Title                     | Platform                | Tag                 |Game Version       | Supported?      |
| ------------------------------ | ----------------------- | ------------------- | ----------------- | --------------- |
| V Version!                     | PlayStation Vita        | PSV                 | Any               | ⭕ PLANNED      |
| Dokodon! Mystery Adventure     | Nintendo 3DS            | 3DS3                | Any               | ⭕ PLANNED      |
| Nijiiro Ver.                   | Arcade                  | AC16                | N/A               | ❌ NOT PLANNED  |
| Rhythm Festival                | Nintendo Switch         | NS2 (JP/ASIA)       | N/A               | ❌ NOT PLANNED  |
| The Drum Master                | PC, Xbox One, Series SX | TDMX, XB1 (N/A)     | N/A               | ❌ NOT PLANNED  |

A version of this tool with all song data can be found elsewhere.  

There's 3 options to sort songs by: ID (A-Z), Song Name (A-Z) and Genre   

This is still a work in-progress, so please report any issues found to me, along with suggestions for features or game support.  

Prerequisites:  
Python 3.12.3 or newer  
tkinter installed through pip `pip install tk`  
sv_ttk installed through pip  `pip install sv_ttk`  
cryptography installed through pip `pip install cryptography`  
pillow installed through pip `pip install pillow`  
numpy installed through pip `pip install numpy`  
pydub installed through pip `pip install pydub`  
ffplay installed in `path`.  
Song Data properly converted to the format this tool expects, stored in a folder called `data` or `data_custom`.  

Due to copyright reasons, etc. no song data will be provided with this tool, however you can use [TjaBatchConvert](https://github.com/cainan-c/TaikoPythonTools/tree/main/TjaBatchConvert)  to convert custom charts to a format this tool expects.  

### Known Issues
Due to how texture conversion is handled, not many songs can be added to the Taiko Wii U games, due to it's texture limit.  
Assuming no official DLC is installed, roughly 90 songs can be added as custom DLC before the game begins to break graphically.  

### Additional Features  
Multi-Language Support. (Can be set in config.json, supports en(English) and jp(Japanese)).  
Custom Song Data loading through the "data_custom" folder. (Path can be changed in config.json).  

![song conversion tool](https://i.imgur.com/YRXb0NA.png)  

## Tools Used
at9tool - Used to convert audio to the Sony AT9 format.  
DRPRepacker from [Pokken-Tools](https://github.com/Sammi-Husky/Pokken-Tools)
[VGAudioCli](https://github.com/Thealexbarney/VGAudio) - Used to convert audio to Nintendo IDSP and Nintendo OPUS.   
[G.722.1 Reference Tool](https://www.itu.int/rec/T-REC-G.722.1-200505-I/en) - Used to convert audio to Polycom Siren 14   

### Special Thanks
Steam User [descatal](https://steamcommunity.com/id/descatal) for writing [this](https://exvsfbce.home.blog/2020/02/04/guide-to-encoding-bnsf-is14-audio-files-converting-wav-back-to-bnsf-is14/) guide on how to create/encode `bnsf` files.   
[korenkonder](https://github.com/korenkonder) for compiling the G.722.1 tool used in this project.  
[Kamui/despairoharmony](https://github.com/despairoharmony) for some of the Nijiiro `.nus3bank` template research.  
[rdbende](https://github.com/rdbende) for the [Sun Valley ttk Theme](https://github.com/rdbende/Sun-Valley-ttk-theme) used in this project.  
[jam1garner](https://github.com/jam1garner) for [Smash-Forge](https://github.com/jam1garner/Smash-Forge), which it's code was used as a reference for generating the `.nut` files.

## Related Tools
[tja2fumen](https://github.com/vivaria/tja2fumen)  
[TjaOffsetNeutralise](https://github.com/cainan-c/TaikoPythonTools/tree/main/TjaOffsetNeutralise)  
[TjaBatchConvert](https://github.com/cainan-c/TaikoPythonTools/tree/main/TjaBatchConvert)  

## Taiko no Tatsujin Modding Server
For help, questions inquries feel free to check out my (Taiko Modding Discord Server)[https://discord.gg/HFm37aA5zr]  
