import os
import sys
import json
from PIL import Image, ImageDraw, ImageFont

# Define a dictionary for vertical forms of certain punctuation marks
rotated_chars = {
    '「': '﹁', '」': '﹂',
    '『': '﹃', '』': '﹄',
    '（': '︵', '）': '︶',
    '［': '﹇', '］': '﹈'
}

def get_text_bbox(draw, text, font):
    return draw.textbbox((0, 0), text, font=font)

def generate_image(draw, text, font, rotated_font, size, position, alignment, stroke_width, stroke_fill, fill, vertical=False, vertical_small=False):
    width, height = size

    # Calculate initial text dimensions
    text_bbox = get_text_bbox(draw, text, font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    if vertical or vertical_small:
        text_height = 0
        max_char_width = 0
        for char in text:
            char_font = rotated_font if char in rotated_chars else font
            char = rotated_chars.get(char, char)
            text_bbox = get_text_bbox(draw, char, char_font)
            text_height += text_bbox[3] - text_bbox[1]
            char_width = text_bbox[2] - text_bbox[0]
            if char_width > max_char_width:
                max_char_width = char_width

        text_height = max(0, text_height - 1)  # Remove the last extra space
        text_position = (position[0] - max_char_width / 2, (height - text_height) / 2)
    else:
        text_bbox = get_text_bbox(draw, text, font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        if alignment == 'center':
            text_position = ((width - text_width) / 2, position[1])
        elif alignment == 'right':
            text_position = (width - text_width, position[1])
        else:
            text_position = position

    if vertical:
        y_offset = 5
        for char in text:
            char_font = rotated_font if char in rotated_chars else font
            char = rotated_chars.get(char, char)
            text_bbox = get_text_bbox(draw, char, char_font)
            char_height = 40
            char_width = text_bbox[2] - text_bbox[0]
            draw.text((text_position[0] - char_width / 2, y_offset), char, font=char_font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
            y_offset += char_height
    elif vertical_small:
        y_offset = text_position[1]
        for char in text:
            char_font = rotated_font if char in rotated_chars else font
            char = rotated_chars.get(char, char)
            text_bbox = get_text_bbox(draw, char, char_font)
            char_height = 27
            char_width = text_bbox[2] - text_bbox[0]
            draw.text((text_position[0] - char_width / 2, y_offset), char, font=char_font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
            y_offset += char_height            
    else:
        draw.text(text_position, text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)

def create_images(data, id, genreNo, font_path, rotated_font_path):
    font_size_extra_large = 46.06875 
    font_size_large = 40.60875 
    font_size_medium = 27.3
    font_size_small = 21.84 

    folder_name = id
    os.makedirs(folder_name, exist_ok=True)

    # Define genre colors
    genre_colors = [
        (0, 78, 88),    # pop
        (159, 61, 2),   # anime
        (90, 98, 129),  # vocaloid
        (55, 74, 0),    # variety        
        (0, 0, 0),      # unused (kids)
        (115, 77, 0),   # classic
        (82, 32, 115),  # game music
        (156, 36, 8),   # namco original
    ]

    genre_color = genre_colors[genreNo]

    # Initialize text variables
    japanese_text = ""
    japanese_sub_text = ""

    # Find the relevant texts
    for item in data['items']:
        if item['key'] == f'song_{id}':
            japanese_text = item['japaneseText']
        if item['key'] == f'song_sub_{id}':
            japanese_sub_text = item['japaneseText']

    # Check if texts were found
    if not japanese_text:
        print(f"Error: No Japanese text found for song_{id}")
        return
    if not japanese_sub_text:
        print(f"Warning: No Japanese sub text found for song_sub_{id}")

    font_extra_large = ImageFont.truetype(font_path, int(font_size_extra_large))
    font_large = ImageFont.truetype(font_path, int(font_size_large))
    font_medium = ImageFont.truetype(font_path, int(font_size_medium))
    font_small = ImageFont.truetype(font_path, int(font_size_small))
    rotated_font = ImageFont.truetype(rotated_font_path, int(font_size_medium))

    # Image 0.png
    img0 = Image.new('RGBA', (720, 64), color=(0, 0, 0, 0))
    draw0 = ImageDraw.Draw(img0)
    generate_image(draw0, japanese_text, font_large, rotated_font, (720, 64), (17, 10), 'right', 5, 'black', 'white')
    img0.save(os.path.join(folder_name, '0.png'))

    # Image 1.png
    img1 = Image.new('RGBA', (720, 104), color=(0, 0, 0, 0))
    draw1 = ImageDraw.Draw(img1)
    generate_image(draw1, japanese_text, font_extra_large, rotated_font, (720, 104), (0, 13), 'center', 5, 'black', 'white')
    generate_image(draw1, japanese_sub_text, font_medium, rotated_font, (720, 104), (0, 68), 'center', 4, 'black', 'white')
    img1.save(os.path.join(folder_name, '1.png'))

    # Image 2.png
    img2 = Image.new('RGBA', (720, 64), color=(0, 0, 0, 0))
    draw2 = ImageDraw.Draw(img2)
    generate_image(draw2, japanese_text, font_large, rotated_font, (720, 64), (0, 4), 'center', 5, 'black', 'white')
    img2.save(os.path.join(folder_name, '2.png'))

    # Image 3.png
    img3 = Image.new('RGBA', (96, 400), color=(0, 0, 0, 0))
    draw3 = ImageDraw.Draw(img3)
    generate_image(draw3, japanese_text, font_large, rotated_font, (96, 400), (89, 0), 'center', 5, 'black', 'white', vertical=True)
    generate_image(draw3, japanese_sub_text, font_medium, rotated_font, (96, 400), (32, 156), 'center', 4, 'black', 'white', vertical_small=True)
    img3.save(os.path.join(folder_name, '3.png'))

    # Image 4.png
    img4 = Image.new('RGBA', (56, 400), color=(0, 0, 0, 0))
    draw4 = ImageDraw.Draw(img4)
    generate_image(draw4, japanese_text, font_large, rotated_font, (56, 400), (48, 0), 'center', 5, genre_color, 'white', vertical=True)
    img4.save(os.path.join(folder_name, '4.png'))

    # Image 5.png
    img5 = Image.new('RGBA', (56, 400), color=(0, 0, 0, 0))
    draw5 = ImageDraw.Draw(img5)
    generate_image(draw5, japanese_text, font_large, rotated_font, (56, 400), (48, 0), 'center', 5, 'black', 'white', vertical=True)
    img5.save(os.path.join(folder_name, '5.png'))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: generate.py <id> <genreNo>")
        sys.exit(1)

    id = sys.argv[1]
    try:
        genreNo = int(sys.argv[2])
        if (genreNo < 0 or genreNo >= 8):
            raise ValueError
    except ValueError:
        print("Error: genreNo must be an integer between 0 and 7")
        sys.exit(1)

    wordlist_path = 'resources/wordlist.json'
    font_path = 'resources/DFPKanTeiRyu-XB.ttf'
    rotated_font_path = 'resources/KozGoPr6NRegular.otf'  # Add the path to your rotated font here

    if not os.path.isfile(wordlist_path):
        print(f"Error: {wordlist_path} not found")
        sys.exit(1)

    if not os.path.isfile(font_path):
        print(f"Error: {font_path} not found")
        sys.exit(1)

    if not os.path.isfile(rotated_font_path):
        print(f"Error: {rotated_font_path} not found")
        sys.exit(1)

    with open(wordlist_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    create_images(data, id, genreNo, font_path, rotated_font_path)
