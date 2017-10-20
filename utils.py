import re

emoji_pattern = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
                           "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002060]+")


def str_human_int(x):
    try:
        int(x)
    except ValueError:
        return None

    if abs(x) < 10000:
        return '%d' % x
    i = 0
    while abs(round(x)) >= 1000 and i < 3:
        x /= 1000
        i += 1
    suffix = ['', 'k', 'M', 'T'][i]

    if abs(round(x)) >= 100 or suffix == '':
        return '{:.0f}{}'.format(x, suffix)
    elif abs(round(x)) >= 10:
        return '{:.1f}{}'.format(x, suffix)
    else:
        return '{:.2f}{}'.format(x, suffix)


def round_int(x):
    if x <= 10:
        return x
    digs = len(str(x))
    base = x / (10 ** (digs-1))
    if base < 2.5:
        return 10 ** (digs-1)
    elif base < 7.5:
        return 5 * 10 ** (digs-1)
    else:
        return 10 ** digs


def int_to_hash(uid):
    uid = (uid + (uid << 32)) ^ 0xB7E151628AED2A6B
    return hex(uid)[2:]


def hash_to_int(hex_str):
    xor_id = int(hex_str, 16)
    return (xor_id ^ 0xB7E151628AED2A6B) >> 32


def strip_emoji(text):
    return emoji_pattern.sub('', text)
