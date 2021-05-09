from ecdsa import VerifyingKey, SigningKey, SECP256k1  # noqa
from ecdsa.util import sigdecode_der, randrange_from_seed__trytryagain
from binascii import unhexlify


def check_signature_ecdsa(pb_key: str, sig: str, message: str) -> bool:
    vk = VerifyingKey.from_string(unhexlify(pb_key))
    result = vk.verify_digest(sig, message, sigdecode=sigdecode_der)
    return result


def generate_pair_from_seeed(seed: bytes):
    prk = SigningKey.from_secret_exponent(randrange_from_seed__trytryagain(seed, order=SECP256k1.order),
                                          curve=SECP256k1)
    return prk, prk.verifying_key
