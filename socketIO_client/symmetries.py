import six


def get_character(x, index):
    return chr(get_byte(x, index))


def get_byte(x, index):
    return six.indexbytes(x, index)


def encode_string(x):
    return x.encode('utf-8')


def decode_string(x):
    return x.decode('utf-8')
