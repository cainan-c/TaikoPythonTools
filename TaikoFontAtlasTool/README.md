# Taiko no Tatsujin - Font to Atlas Texture  

Usage: font_to_atlas.py [-h] ttf_path font_size image_width image_height {ascii,unicode} output_name  

Convert TTF font to texture and XML  

Positional arguments:  
  ttf_path         Path to the TTF font file  
  font_size        Font size  
  image_width      Width of the texture image  
  image_height     Height of the texture image  
  {ascii,unicode}  Character range  
  output_name      Output name (e.g., en_64)  

Should support any NU Library Taiko game which pairs a texture atlas and xml file for it's font. (NS1, PS4 and Arcade).   
Possibly may also support non-Taiko NU Library titles also.  