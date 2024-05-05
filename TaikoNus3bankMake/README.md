# Taiko no Tatsujin - Nus3bank Creation Tool

Python 3 scripts that converts audio to a Taiko no Tatsujin compatable `.nus3bank` file.  
Accepted file types: `.mp3`, `.wav`, `.flac` and whatever else pydub supports.  

```
usage: conv.py [-h] [input_audio] [audio_type] [game] [preview_point] [song_id]

Convert audio to nus3bank

positional arguments:
  input_audio    Input audio file path.
  audio_type     Type of input audio (e.g., bnsf, at9, idsp, lopus).
  game           Game type (e.g., nijiiro, ns1, ps4).
  preview_point  Audio preview point in ms.
  song_id        Song ID for the nus3bank file.
```

By default includes support for Taiko no Tatsujin Wii U 3, NS1, PS4 and Nijiiro.  
Support for other Taiko no Tatsujin games that use `.nus3bank` can be added in the future.  

### Prerequisites 
[Python 3.12.3](https://www.python.org/downloads/) or newer installed.  
Python 3 Module pydub `pip install pydub`  

### Supported Audio Formats

| Audio Format  | NS1           | PS4           | WIIU3         | Nijiiro       |
| ------------- | ------------- | ------------- | ------------- | ------------- |
| WAV (PCM)     | ✅           | ✅            | ✅            | ✅           |
| BNSF (IS14)   | ✅           | ✅            | ❓            | ✅           |
| Nintendo OPUS | ✅           | ❌            | ❌            | ❌           |
| Nintendo IDSP | ✅           | ❌            | ✅            | ✅           |
| Sony AT9      | ❌           | ✅            | ❌            | ❌           |

### Known Limitations
It seems that if a IS14 BNSF .nus3bank file is too long/too large in size, then it'll fail to play in "Song Select", even if the "Preview Point" is properly set.

Due to the limitations of the format, IS14 only supports MONO audio and a rather low bitrate. As a result, the audio quality is rather low.  

When it comes to Song ID:  
Nijiiro can have Song IDs ranging from 3 to 8 characters.  
Wii U, PS4 and NS1 can only have Song IDs ranging from 3 to 6 characters.  
Exceeding this will result in an error.

## Tools Used
at9tool - Used to convert audio to the Sony AT9 format.  
[VGAudioCli](https://github.com/Thealexbarney/VGAudio) - Used to convert audio to Nintendo IDSP and Nintendo OPUS.   
[G.722.1 Reference Tool](https://www.itu.int/rec/T-REC-G.722.1-200505-I/en) - Used to convert audio to Polycom Siren 14   

### Special Thanks
Steam User [descatal](https://steamcommunity.com/id/descatal) for writing [this](https://exvsfbce.home.blog/2020/02/04/guide-to-encoding-bnsf-is14-audio-files-converting-wav-back-to-bnsf-is14/) guide on how to create/encode `bnsf` files. 
[korenkonder](https://github.com/korenkonder) for compiling the G.722.1 tool used in this project.
[Kamui/despairoharmony](https://github.com/despairoharmony) for some of the Nijiiro `.nus3bank` template research.
