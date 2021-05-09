import ecdsa


def verify_ecdsa(sig: str, pb_key: str):
    vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(pb_key))
    try:
        vk.verify(bytes.fromhex(sig))
        return True
    except ecdsa.BadSignatureError:
        return False
