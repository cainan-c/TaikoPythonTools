import argparse
import os
from PIL import Image
import struct

class TextureSurface:
    def __init__(self):
        self.mipmaps = []

class NutTexture:
    def __init__(self, width, height, pixel_format, pixel_type):
        self.surfaces = [TextureSurface()]
        self.Width = width
        self.Height = height
        self.pixelInternalFormat = pixel_format
        self.pixelFormat = pixel_type

    def add_mipmap(self, mipmap_data):
        self.surfaces[0].mipmaps.append(mipmap_data)

    @property
    def MipMapsPerSurface(self):
        return len(self.surfaces[0].mipmaps)

    def getNutFormat(self):
        if self.pixelInternalFormat == 'RGBA':
            return 14
        raise NotImplementedError("Only RGBA format is implemented")

class NUT:
    def __init__(self):
        self.textures = []

    def add_texture(self, texture):
        self.textures.append(texture)

    def save(self, filename):
        with open(filename, 'wb') as f:
            f.write(self.build())

    def build(self):
        data = bytearray()
        num_textures = len(self.textures)
        # File header
        header = struct.pack(">IHH", 0x4E545033, 0x0200, num_textures)
        data.extend(header)

        # Initial offset (0x18 bytes for the header, then 0x4 bytes per texture offset)
        texture_offset_base = 0x18 + (0x4 * num_textures)
        texture_headers_offset = texture_offset_base
        texture_data_offset = texture_headers_offset + (0x50 * num_textures)

        # Ensure texture data starts at the correct offset (0x42E0)
        texture_data_offset = max(texture_data_offset, 0x4000)

        # Offset table
        texture_offsets = []
        for texture in self.textures:
            texture_offsets.append(texture_data_offset)
            texture_data_offset += 0x50 + sum(len(mipmap) for mipmap in texture.surfaces[0].mipmaps)

        for offset in texture_offsets:
            data.extend(struct.pack(">I", offset))
        
        # Texture headers and mipmaps
        for texture, offset in zip(self.textures, texture_offsets):
            data.extend(self.build_texture_header(texture, offset))
        
        for texture in self.textures:
            for mipmap in texture.surfaces[0].mipmaps:
                data.extend(mipmap)

        return data

    def build_texture_header(self, texture, offset):
        mipmap_count = texture.MipMapsPerSurface
        size = texture.Width * texture.Height * 4  # Texture size
        header = struct.pack(">IIIIHHIIII",
                             size, texture.Width, texture.Height, 0, 0,
                             mipmap_count, texture.getNutFormat(),
                             texture.Width, texture.Height, 0)
        additional_data = b'\x65\x58\x74\x00\x00\x00\x00\x20\x00\x00\x00\x10\x00\x00\x00\x00' \
                          b'\x47\x49\x44\x58\x00\x00\x00\x10\x00\x00\x00\x05\x00\x00\x00\x00'
        return header + additional_data.ljust(0x50 - len(header), b'\x00')

    def modify_nut_file(self, file_path, output_path):
        # Set replacement bytes to 00

        with open(file_path, 'rb') as f:
            data = bytearray(f.read())
        
        # Replace bytes from 0x00 to 0x1F0
        #data[0x00:0x1EF] = replacement_bytes
        # Delete bytes from 0x42E0 to 0x42F3 (0x42E0 to 0x42F4 inclusive)
        del data[0x42E0:0x42F3]
        del data[0x0040:0x0044]
        data[0x1F0:0x1F0] = b'\x00\x00\x00\x00'
        data[0x008:0x010] = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        data[0x010:0x040] = b'\x00\x02\xd0P\x00\x00\x00\x00\x00\x02\xd0\x00\x00P\x00\x00\x00\x01\x00\x0e\x02\xd0\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\xe0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data[0x060:0x090] = b'\x00\x04\x92P\x00\x00\x00\x00\x00\x04\x92\x00\x00P\x00\x00\x00\x01\x00\x0e\x02\xd0\x00h\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xd1\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data[0x0B0:0x0E0] = b'\x00\x02\xd0P\x00\x00\x00\x00\x00\x02\xd0\x00\x00P\x00\x00\x00\x01\x00\x0e\x02\xd0\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07c@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data[0x100:0x130] = b'\x00\x02X\x50\x00\x00\x00\x00\x00\x02X\x00\x00P\x00\x00\x00\x01\x00\x0e\x00`\x01\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\n2\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data[0x150:0x180] = b'\x00\x01^P\x00\x00\x00\x00\x00\x01^\x00\x00P\x00\x00\x00\x01\x00\x0e\x00\x38\x01\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x8a\xa0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data[0x1A0:0x1D0] = b'\x00\x01^P\x00\x00\x00\x00\x00\x01^\x00\x00P\x00\x00\x00\x01\x00\x0e\x00\x38\x01\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\r\xe8P\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data[0x5B:0x5C] = b'\x00'
        data[0xAB:0xAC] = b'\x01'
        data[0xFB:0xFC] = b'\x02'
        data[0x14B:0x14C] = b'\x03'
        data[0x19B:0x19C] = b'\x04'
        # Add three 0x00 bytes to the end of the file
        data.extend(b'\x00\x00\x00')

        with open(output_path, 'wb') as f:
            f.write(data)

def load_png_to_texture(filepath):
    with Image.open(filepath) as img:
        img = img.convert("RGBA")
        width, height = img.size
        mipmap_data = img.tobytes()
        texture = NutTexture(width, height, "RGBA", "RGBA")
        texture.add_mipmap(mipmap_data)
        return texture

def main():
    parser = argparse.ArgumentParser(description="Convert a folder of PNGs to a NUT file.")
    parser.add_argument("input_folder", help="Folder containing PNG files")
    parser.add_argument("output_file", help="Output NUT file")
    args = parser.parse_args()

    nut = NUT()
    for filename in os.listdir(args.input_folder):
        if filename.endswith(".png"):
            texture = load_png_to_texture(os.path.join(args.input_folder, filename))
            nut.add_texture(texture)

    # Save the NUT file
    nut_filename = args.output_file
    nut.save(nut_filename)

    # Modify the saved NUT file
    output_filename = nut_filename  # You can modify this if needed
    nut.modify_nut_file(nut_filename, output_filename)

if __name__ == "__main__":
    main()
