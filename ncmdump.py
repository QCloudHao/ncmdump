# -*- coding: utf-8 -*-
__author__ = 'qyh'
__date__ = '2022/3/31 9:52'

import binascii
import struct
import base64
import json
import os
import sys
from Crypto.Cipher import AES

NCM_SUFFIX = '.ncm'
AUDIO_SUFFIX = ['.mp3', '.flac']


def unpad(s):
    return s[0:-(s[-1] if type(s[-1]) == int else ord(s[-1]))]


def dump(file_path):
    # AES key
    core_key = binascii.a2b_hex("687A4852416D736F356B496E62617857")
    meta_key = binascii.a2b_hex("2331346C6A6B5F215C5D2630553C2728")

    # read magic header
    f = open(file_path, 'rb')
    header = f.read(8)
    # str to hex
    assert binascii.b2a_hex(header) == b'4354454e4644414d'

    # read key length
    f.seek(2, 1)
    key_length = f.read(4)
    key_length = struct.unpack('<I', bytes(key_length))[0]

    # read key
    key_data = f.read(key_length)
    key_data_array = bytearray(key_data)
    for i in range(0, len(key_data_array)):
        key_data_array[i] ^= 0x64
    key_data = bytes(key_data_array)
    cryptor = AES.new(core_key, AES.MODE_ECB)
    key_data = unpad(cryptor.decrypt(key_data))[17:]
    key_length = len(key_data)
    key_data = bytearray(key_data)
    key_box = bytearray(range(256))
    c = 0
    last_byte = 0
    key_offset = 0
    for i in range(256):
        swap = key_box[i]
        c = (swap + last_byte + key_data[key_offset]) & 0xff
        key_offset += 1
        if key_offset >= key_length:
            key_offset = 0
        key_box[i] = key_box[c]
        key_box[c] = swap
        last_byte = c

    # read meta length
    meta_length = f.read(4)
    meta_length = struct.unpack('<I', bytes(meta_length))[0]

    # read meta
    meta_data = f.read(meta_length)
    meta_data_array = bytearray(meta_data)
    for i in range(0, len(meta_data_array)):
        meta_data_array[i] ^= 0x63
    meta_data = bytes(meta_data_array)
    meta_data = base64.b64decode(meta_data[22:])
    cryptor = AES.new(meta_key, AES.MODE_ECB)
    meta_data = unpad(cryptor.decrypt(meta_data)).decode('utf-8')[6:]
    meta_data = json.loads(meta_data)

    # read crc
    crc32 = f.read(4)
    crc32 = struct.unpack('<I', bytes(crc32))[0]
    f.seek(5, 1)

    # read image size
    image_size = f.read(4)
    image_size = struct.unpack('<I', bytes(image_size))[0]

    # read image data
    f.read(image_size)

    # read music data
    file_name = f.name.split("/")[-1].replace('.ncm', f".{meta_data['format']}")
    m = open(os.path.join(os.path.split(file_path)[0], file_name), 'wb')
    chunk = bytearray()
    while True:
        chunk = bytearray(f.read(0x8000))
        if not chunk:
            break
        for i in range(1, len(chunk)+1):
            j = i & 0xff
            chunk[i-1] ^= key_box[(key_box[j] + key_box[(key_box[j] + j) & 0xff]) & 0xff]
        m.write(chunk)
    m.close()
    f.close()
    return file_name


if __name__ == '__main__':
    args = sys.argv[1:]

    if not args:
        print('Usage: \n  python3 ncmdump.py <ncm_folder_path>\n  Add "-o" to override.')
        exit(1)

    folder = args[0]
    override = '-o' == args[1] if len(args) > 1 else False

    file_list = []
    for file in os.listdir(folder):
        if file.endswith(NCM_SUFFIX):
            if not override:
                have = False
                for suffix in AUDIO_SUFFIX:
                    if os.path.exists(os.path.join(folder, file.replace(NCM_SUFFIX, suffix))):
                        have = True
                        break
                if have:
                    continue
            file_list.append(os.path.join(folder, file))

    convert_length = len(file_list)
    if convert_length == 0:
        print(f"No .ncm files need to be converted.\nUse 'python3 ncmdump.py {folder} -o' to override.")
        exit(0)

    for index, file in enumerate(file_list):
        try:
            print(f'[{index}/{convert_length}]  {dump(file)}')
        except KeyboardInterrupt as e:
            if 'm.write(chunk)' in str(e):
                for suffix in AUDIO_SUFFIX:
                    file_path = os.path.join(folder, file.replace(NCM_SUFFIX, suffix))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f'\nDue to KeyboardInterrupt\n{file_path} is removed.')
            exit(0)
