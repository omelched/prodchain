from binascii import hexlify
from hashlib import sha256

from Crypto.Hash import RIPEMD160, keccak  # noqa


def dsha256(payload: str):
    return sha256(sha256(payload.encode('utf-8')).digest()).hexdigest()


def sha256ripemd160(payload: str):
    return RIPEMD160.new(hexlify(sha256(payload.encode('utf-8')).digest())).hexdigest()


def keccak_hash(data):
    _kh = keccak.new(digest_bits=256)
    _kh.update(data)
    return _kh.hexdigest()
