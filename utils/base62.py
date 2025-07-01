import string

ALPHABET = string.digits + string.ascii_letters

def base62_decode(s):
    base = len(ALPHABET)
    num = 0
    for char in s:
        num = num * base + ALPHABET.index(char)
    return num
