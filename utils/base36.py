def base36_encode(number):
    chars = '0123456789abcdefghijklmnopqrstuvwxyz'
    if number == 0:
        return '0'
    result = ''
    while number:
        number, i = divmod(number, 36)
        result = chars[i] + result
    return result

def base36_decode(s):
    return int(s, 36)
