import re

rgb_pattern = re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')


def is_rgb_hex(value):
    return bool(rgb_pattern.match(value))


def hex_to_rgb(hex_string):
    hex_string = hex_string.lstrip('#')
    hex_len = len(hex_string)
    return tuple(int(hex_string[i:i + int(hex_len / 3)], 16) for i in range(0, hex_len, int(hex_len / 3)))
