import hashlib
import base64
import uuid

# Constants
BLOCK_SIZE = 16

def pad(data):
    padding_length = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
    padding = chr(padding_length) * padding_length
    return data + padding

def unpad(data):
    padding_length = ord(data[-1])
    return data[:-padding_length]

def generate_key(password):
    return hashlib.sha256(password).digest()

def simple_encrypt(key, plaintext):
    plaintext = pad(plaintext)
    encrypted = ''.join(chr(ord(x) ^ ord(y)) for (x, y) in zip(plaintext, key))
    return base64.urlsafe_b64encode(encrypted)

def simple_decrypt(key, encrypted):
    encrypted = base64.urlsafe_b64decode(encrypted)
    decrypted = ''.join(chr(ord(x) ^ ord(y)) for (x, y) in zip(encrypted, key))
    return unpad(decrypted)

def get_mac_address():
    mac = uuid.getnode()
    mac_str = ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
    return mac_str