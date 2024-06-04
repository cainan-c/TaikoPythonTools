import os
import argparse
from PIL import Image, ImageFont, ImageDraw
import xml.etree.ElementTree as ET

def ttf_to_texture_and_xml(ttf_path, output_image_path, output_xml_path, font_size=48, image_width=4096, image_height=512, padding=1, extra_padding=1, y_padding=2, char_range='ascii'):
    # Create a new image with transparent background
    image = Image.new("RGBA", (image_width, image_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    # Load the font
    font = ImageFont.truetype(ttf_path, font_size)

    # Initialize XML structure
    root_element = ET.Element("root")
    font_element = ET.SubElement(root_element, "font", texWidth=str(image_width), texHeight=str(image_height), 
                                 fontSize=str(font_size), fontPoint=str(font_size), fixedHalfWidth="32", glyphNum="0")

    # Draw each character and add to XML
    x = padding + extra_padding
    y = padding + extra_padding + y_padding
    char_count = 0
    tallest_char_height = 0  # To store the height of the tallest character

    start = 0
    end = 256 if char_range == 'ascii' else 65536

    for i in range(start, end):  # Unicode range
        char = chr(i)
        try:
            bbox = draw.textbbox((0, 0), char, font=font)
        except Exception:
            continue
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        tallest_char_height = max(tallest_char_height, height)  # Update tallest character height
        
        # Check if the character fits in the current row, otherwise move to next row
        if x + width + padding + extra_padding > image_width:
            x = padding + extra_padding
            y += tallest_char_height + 2 * (padding + extra_padding)  # Use tallest char height
            tallest_char_height = 0  # Reset tallest char height for new row
        
        # Check if the character fits in the current column, otherwise skip
        if y + tallest_char_height + padding + extra_padding > image_height:
            break

        draw.text((x, y), char, font=font, fill="white")

        glyph_element = ET.SubElement(font_element, "glyph", 
                                     index=str(i), 
                                     type="1", 
                                     offsetU=str(x), 
                                     offsetV=str(y), 
                                     width=str(width), 
                                     height=str(tallest_char_height))  # Use tallest char height
        x += width + 2 * (padding + extra_padding)
        char_count += 1

    # Update glyphNum in XML
    font_element.set("glyphNum", str(char_count))

    # Save the image
    image.save(output_image_path)

    # Save the XML with specific formatting
    tree = ET.ElementTree(root_element)
    tree.write(output_xml_path, encoding="utf-8", xml_declaration=True)

    # Format the XML file to match the provided structure
    import xml.dom.minidom
    xml_str = xml.dom.minidom.parseString(ET.tostring(root_element)).toprettyxml(indent="  ")
    with open(output_xml_path, "w", encoding="utf-8") as f:
        f.write(xml_str.replace('<?xml version="1.0" ?>', '').strip())

def main():
    parser = argparse.ArgumentParser(description="Convert TTF font to texture and XML")
    parser.add_argument("ttf_path", type=str, help="Path to the TTF font file")
    parser.add_argument("font_size", type=int, help="Font size")
    parser.add_argument("image_width", type=int, help="Width of the texture image")
    parser.add_argument("image_height", type=int, help="Height of the texture image")
    parser.add_argument("char_range", choices=['ascii', 'unicode'], default='ascii', help="Character range")
    parser.add_argument("output_name", type=str, help="Output name (e.g., en_64)")
    args = parser.parse_args()

    output_image_path = os.path.join("out", f"{args.output_name}.png")
    output_xml_path = os.path.join("out", f"{args.output_name}.xml")

    ttf_to_texture_and_xml(args.ttf_path, output_image_path, output_xml_path, args.font_size, args.image_width, args.image_height, char_range=args.char_range)

if __name__ == "__main__":
    main()
