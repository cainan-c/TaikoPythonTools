# Taiko no Tatsujin Wii U Texture Tool

Tool to generate song textures for Taiko no Tatsujin Wii U 1-3, using a modern wordlist.json file.  
Only supports Japanese text for now.  

`Usage: generate.py <id> <genreNo> [-ura]`

There is also an additional script in here to convert the folder of textures to a .nut texture.
The code in this was partially based on the NUT code found in [Smash Forge](https://github.com/jam1garner/Smash-Forge) 

```
Usage: generate_nut.py [-h] [--format {dxt1,dxt3,dxt5}] input_folder output_file

Generate NUT file from PNG files.

positional arguments:
  input_folder          Input folder containing PNG files.
  output_file           Output NUT file.

options:
  -h, --help            show this help message and exit
  --format {dxt1,dxt3,dxt5}
                        Texture compression format.
```

Requirements:
[NVIDIA Texture Tools Exporter](https://developer.nvidia.com/texture-tools-exporter) installed and added to PATH  