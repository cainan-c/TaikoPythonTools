import argparse
import os
import struct
import subprocess
#from PIL import Image

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
        self.HashId = 0

    def add_mipmap(self, mipmap_data):
        self.surfaces[0].mipmaps.append(mipmap_data)

    @property
    def MipMapsPerSurface(self):
        return len(self.surfaces[0].mipmaps)

    def getNutFormat(self):
        if self.pixelInternalFormat == 'CompressedRgbaS3tcDxt1Ext':
            return 0
        elif self.pixelInternalFormat == 'CompressedRgbaS3tcDxt3Ext':
            return 1
        elif self.pixelInternalFormat == 'CompressedRgbaS3tcDxt5Ext':
            return 2
        elif self.pixelInternalFormat == 'RGBA':
            if self.pixelFormat == 'RGBA':
                return 14
            elif self.pixelFormat == 'ABGR':
                return 16
            else:
                return 17
        else:
            raise NotImplementedError(f"Unknown pixel format {self.pixelInternalFormat}")

class NUT:
    def __init__(self):
        self.textures = []
        self.endian = 'big'
        self.version = 0x0200

    def add_texture(self, texture):
        self.textures.append(texture)

    def save(self, filename):
        with open(filename, 'wb') as f:
            f.write(self.build())

    def build(self):
        o = bytearray()
        data = bytearray()

        if self.endian == 'big':
            o.extend(struct.pack('>I', 0x4E545033))  # NTP3
        else:
            o.extend(struct.pack('>I', 0x4E545744))  # NTWD

        if self.version > 0x0200:
            self.version = 0x0200

        o.extend(struct.pack('>H', self.version))
        num_textures = len(self.textures)
        if num_textures != 1 and num_textures != 6:
            raise ValueError("The number of images must be either 1 or 6.")
        o.extend(struct.pack('>H', num_textures))
        o.extend(b'\x00' * 8)  # Reserved space

        header_length = 0
        for texture in self.textures:
            surface_count = len(texture.surfaces)
            is_cubemap = surface_count == 6
            if surface_count < 1 or surface_count > 6:
                raise NotImplementedError(f"Unsupported surface amount {surface_count} for texture. 1 to 6 faces are required.")
            if surface_count > 1 and surface_count < 6:
                raise NotImplementedError(f"Unsupported cubemap face amount for texture. Six faces are required.")
            mipmap_count = len(texture.surfaces[0].mipmaps)
            header_size = 0x50 + (0x10 if is_cubemap else 0) + (mipmap_count * 4 if mipmap_count > 1 else 0)
            header_size = (header_size + 0xF) & ~0xF  # Align to 16 bytes
            header_length += header_size

        for texture in self.textures:
            surface_count = len(texture.surfaces)
            is_cubemap = surface_count == 6
            mipmap_count = len(texture.surfaces[0].mipmaps)

            data_size = sum((len(mipmap) + 0xF) & ~0xF for mipmap in texture.surfaces[0].mipmaps)
            header_size = 0x50 + (0x10 if is_cubemap else 0) + (mipmap_count * 4 if mipmap_count > 1 else 0)
            header_size = (header_size + 0xF) & ~0xF

            o.extend(struct.pack('>I', data_size + header_size))
            o.extend(b'\x00' * 4)  # Padding
            o.extend(struct.pack('>I', data_size))
            o.extend(struct.pack('>H', header_size))
            o.extend(b'\x00' * 2)  # Padding

            o.extend(b'\x00')
            o.extend(struct.pack('B', mipmap_count))
            o.extend(b'\x00')
            o.extend(struct.pack('B', texture.getNutFormat()))
            o.extend(struct.pack('>HH', texture.Width, texture.Height))
            o.extend(b'\x00' * 4)  # Padding
            o.extend(struct.pack('>I', 0))  # DDS Caps2 placeholder

            if self.version >= 0x0200:
                o.extend(struct.pack('>I', header_length + len(data)))
            else:
                o.extend(b'\x00' * 4)  # Padding

            header_length -= header_size
            o.extend(b'\x00' * 12)  # Reserved space

            if is_cubemap:
                o.extend(struct.pack('>II', len(texture.surfaces[0].mipmaps[0]), len(texture.surfaces[0].mipmaps[0])))
                o.extend(b'\x00' * 8)  # Padding

            if texture.getNutFormat() == 14 or texture.getNutFormat() == 17:
                self.swap_channel_order_down(texture)

            for surface in texture.surfaces:
                for mipmap in surface.mipmaps:
                    mip_start = len(data)
                    data.extend(mipmap)
                    while len(data) % 0x10 != 0:
                        data.extend(b'\x00')
                    if mipmap_count > 1:
                        mip_end = len(data)
                        o.extend(struct.pack('>I', mip_end - mip_start))

            while len(o) % 0x10 != 0:
                o.extend(b'\x00')

            if texture.getNutFormat() == 14 or texture.getNutFormat() == 17:
                self.swap_channel_order_up(texture)

            o.extend(b'\x65\x58\x74\x00')  # "eXt\0"
            o.extend(struct.pack('>II', 0x20, 0x10))
            o.extend(b'\x00' * 4)

            o.extend(b'\x47\x49\x44\x58')  # "GIDX"
            o.extend(struct.pack('>I', 0x10))
            o.extend(struct.pack('>I', texture.HashId))  # Texture ID
            o.extend(b'\x00' * 4)

        o.extend(data)

        return o

    def swap_channel_order_down(self, texture):
        for surface in texture.surfaces:
            for i, mipmap in enumerate(surface.mipmaps):
                mipmap = bytearray(mipmap)
                for j in range(0, len(mipmap), 4):
                    mipmap[j], mipmap[j + 2] = mipmap[j + 2], mipmap[j]
                surface.mipmaps[i] = bytes(mipmap)

    def swap_channel_order_up(self, texture):
        for surface in texture.surfaces:
            for i, mipmap in enumerate(surface.mipmaps):
                mipmap = bytearray(mipmap)
                for j in range(0, len(mipmap), 4):
                    mipmap[j], mipmap[j + 2] = mipmap[j + 2], mipmap[j]
                surface.mipmaps[i] = bytes(mipmap)

def nvcompress_png_to_dds(png_filepath, dds_filepath, format_option):
    format_map = {
        'dxt1': '-bc1',
        'dxt3': '-bc2',
        'dxt5': '-bc3',
    }
    format_arg = format_map.get(format_option.lower(), '-bc1')
    command = f"nvcompress {format_arg} {png_filepath} {dds_filepath}"
    subprocess.run(command, shell=True, check=True)

def load_dds_to_texture(dds_filepath, index, pixel_format):
    DDS_HEADER_SIZE = 128  # DDS header size in bytes
    with open(dds_filepath, 'rb') as dds_file:
        dds_data = dds_file.read()
        print(f"Length of dds_data: {len(dds_data)}")
        print(f"Bytes from 12 to 20: {dds_data[12:20]}")
        width, height = struct.unpack_from('<II', dds_data, 12)[:2]
        texture = NutTexture(height, width, pixel_format, pixel_format)
        texture.add_mipmap(dds_data[DDS_HEADER_SIZE:])  # Skip the DDS header
        texture.HashId = index  # Set HashId based on the index
        return texture

def generate_nut_from_pngs(png_folder, output_nut_path, format_option):
    nut = NUT()
    png_files = [f for f in os.listdir(png_folder) if f.lower().endswith('.png')]
    for index, png_file in enumerate(png_files):
        png_path = os.path.join(png_folder, png_file)
        dds_path = os.path.splitext(png_path)[0] + '.dds'
        nvcompress_png_to_dds(png_path, dds_path, format_option)
        texture = load_dds_to_texture(dds_path, index, f'CompressedRgbaS3tc{format_option.capitalize()}Ext')
        nut.add_texture(texture)
    nut.save(output_nut_path)

def main():
    parser = argparse.ArgumentParser(description='Generate NUT file from PNG files.')
    parser.add_argument('input_folder', type=str, help='Input folder containing PNG files.')
    parser.add_argument('output_file', type=str, help='Output NUT file.')
    parser.add_argument('--format', type=str, default='dxt5', choices=['dxt1', 'dxt3', 'dxt5'], help='Texture compression format.')
    args = parser.parse_args()

    generate_nut_from_pngs(args.input_folder, args.output_file, args.format)

if __name__ == '__main__':
    main()
