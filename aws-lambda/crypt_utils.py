import hashlib

def md5_encrypt(text):
    m = hashlib.md5()
    m.update(text.encode('utf-8'))
    return m.hexdigest()
