from hashlib import sha256
from binascii import hexlify

from Crypto.Hash import RIPEMD160  # noqa


def dsha256(payload: str):
    return sha256(sha256(payload.encode('utf-8')).digest()).hexdigest()


def sha256ripemd160(payload: str):
    return RIPEMD160.new(hexlify(sha256(payload.encode('utf-8')).digest())).hexdigest()
