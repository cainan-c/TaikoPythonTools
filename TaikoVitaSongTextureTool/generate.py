import os
import sys
import json
from PIL import Image, ImageDraw, ImageFont

# Define a dictionary for vertical forms of certain punctuation marks
rotated_chars = {
    '「': '﹁', '」': '﹂',
    '『': '﹃', '』': '﹄',
    '（': '︵', '）': '︶',
    '［': '﹇', '］': '﹈',
    '〝': '﹁', '〟': '﹂',
    '｛': '︷', '｝': '︸',
    '｟': '︹', '｠': '︺',
    '＜': '︿', '＞': '﹀',
    '《': '︽', '》': '︾',
    '〈': '︿', '〉': '﹀',
    '【': '︻', '】': '︼',
    '〔': '︹', '〕': '︺',
    '「': '﹁', '」': '﹂',
    '『': '﹃', '』': '﹄',
    '（': '︵', '）': '︶',
    '［': '﹇', '］': '﹈',
    '｛': '︷', '｝': '︸',
    '〈': '︿', '〉': '﹀',
    '《': '︽', '》': '︾',
    '【': '︻', '】': '︼',
    '〔': '︹', '〕': '︺'
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
        y_offset = 0
        for char in text:
            char_font = rotated_font if char in rotated_chars else font
            char = rotated_chars.get(char, char)
            text_bbox = get_text_bbox(draw, char, char_font)
            char_height = 25
            char_width = text_bbox[2] - text_bbox[0]
            draw.text((text_position[0] - char_width / 2, y_offset), char, font=char_font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
            y_offset += char_height
    elif vertical_small:
        y_offset = 5
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

def create_images(data, id, font_path, rotated_font_path):
    font_size_extra_large = 28.79296875
    font_size_large = 25.38046875 
    font_size_medium = 17.0625 
    font_size_small = 13.65 

    folder_name = id
    os.makedirs(folder_name, exist_ok=True)

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

    # game
    img0 = Image.new('RGBA', (432, 40), color=(0, 0, 0, 0))
    draw0 = ImageDraw.Draw(img0)
    generate_image(draw0, japanese_text, font_large, rotated_font, (432, 40), (21, 10), 'right', 3, 'black', 'white')
    img0.save(os.path.join(folder_name, 'game.png'))

    # select_sub
    img1_height = 320

    img1 = Image.new('RGBA', (48, 320), color=(0, 0, 0, 0))
    draw1 = ImageDraw.Draw(img1)

    temp_img1 = Image.new('RGBA', (48, 1000), (0, 0, 0, 0))  # Temporary image with 1000px height
    temp_draw1 = ImageDraw.Draw(temp_img1)

    generate_image(temp_draw1, japanese_sub_text, font_large, rotated_font, (48, 320), (37, 0), 'center', 3, 'black', 'white', vertical=True)

    # Crop the temporary image to the actual height of the text
    y_offset = 0
    for char in japanese_sub_text:
        char_font = rotated_font if char in rotated_chars else font_large
        char = rotated_chars.get(char, char)
        text_bbox = get_text_bbox(temp_draw1, char, char_font)
        char_height = 27
        y_offset += char_height

    # Crop the temporary image to the actual height of the text
    temp_img1 = temp_img1.crop((0, 0, 48, y_offset))

    # Resize the image if it exceeds the specified height
    if y_offset > img1_height:
        img1 = temp_img1.resize((48, img1_height), Image.Resampling.LANCZOS)
    else:
        img1 = temp_img1.crop((0, 0, 48, img1_height))

    img1.save(os.path.join(folder_name, 'select_sub.png'))

    # select_main
    img2_height = 320

    img2 = Image.new('RGBA', (48, 320), color=(0, 0, 0, 0))
    draw2 = ImageDraw.Draw(img2)

    temp_img2 = Image.new('RGBA', (48, 1000), (0, 0, 0, 0))  # Temporary image with 1000px height
    temp_draw2 = ImageDraw.Draw(temp_img2)

    generate_image(temp_draw2, japanese_text, font_large, rotated_font, (48, 320), (37, 0), 'center', 3, 'black', 'white', vertical=True)

    # Crop the temporary image to the actual height of the text
    y_offset = 0
    for char in japanese_text:
        char_font = rotated_font if char in rotated_chars else font_large
        char = rotated_chars.get(char, char)
        text_bbox = get_text_bbox(temp_draw2, char, char_font)
        char_height = 27
        y_offset += char_height

    # Crop the temporary image to the actual height of the text
    temp_img2 = temp_img2.crop((0, 0, 48, y_offset))

    # Resize the image if it exceeds the specified height
    if y_offset > img2_height:
        img2 = temp_img2.resize((48, img2_height), Image.Resampling.LANCZOS)
    else:
        img2 = temp_img2.crop((0, 0, 48, img2_height))

    img2.save(os.path.join(folder_name, 'select_main.png'))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: generate.py <id>")
        sys.exit(1)

    id = sys.argv[1]

    wordlist_path = 'resources/wordlist.json'
    font_path = 'resources/DFPKanTeiRyu-XB.ttf'
    rotated_font_path = 'resources/KozGoPr6NRegular.otf'

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

    create_images(data, id, font_path, rotated_font_path)
