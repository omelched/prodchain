from enum import Enum
from typing import Union
import json

from crypto.hashing import dsha256
from crypto.signatures import check_signature_ecdsa


class TransactionTypes(Enum):
    # simple transfer
    transfer = 0x00

    # transfer with confirmation
    transfer_with_confirmation = 0x10
    confirm_transfer = 0x11
    reject_transfer = 0x12
    cancel_transfer = 0x13

    # asset creation
    create_as_import = 0x20

    # asset modification
    create_asset = 0xf0
    delete_asset = 0xf1
    update_asset = 0xf2



    @property
    def value(self):
        return self._value_.to_bytes(1, 'big').hex()


class Transaction(object):
    tx_type: TransactionTypes = None
    sender: str = None
    receiver: str = None
    payload: dict = {}
    signature: str = None
    pub_key: str = None

    @property
    def hash(self):
        return dsha256(self.dump('json-raw'))

    def __init__(self, tx_type: TransactionTypes, sender: str, reciever: Union[str, None], payload: dict,
                 signature: str, pub_key: str, nonce: int):
        assert isinstance(tx_type, TransactionTypes)
        self.tx_type = tx_type
        self.sender = sender
        self.receiver = reciever
        self.payload = payload
        self.nonce = nonce

        self.signature = signature
        self.pub_key = pub_key

        assert self._check_signature()

    def __repr__(self):
        return f'{type(self).__name__}({self.tx_type.value}, {self.sender}, {self.receiver}, {self.payload},' \
               f'{self.signature}, {self.pub_key}, {self.nonce})'

    def _check_signature(self):
        return check_signature_ecdsa(self.pub_key, self.signature, self.hash)

    @staticmethod
    def json_parser_hook(dump: dict):
        assert all(k in dump for k in ('hash', 'tx_type', 'sender', 'receiver',
                                       'payload', 'signature', 'pub_key', 'nonce'))

        return Transaction(
            TransactionTypes(int(dump['tx_type'], 16)),
            dump['sender'],
            dump['reciever'],
            json.loads(dump['payload']),
            dump['signature'],
            dump['pub_key'],
            dump['nonce']
        )

    def dump(self, dump_format: str = 'json'):
        if dump_format == 'json':
            return json.dumps({'hash': self.hash,
                               'tx_type': self.tx_type.value,
                               'sender': self.sender,
                               'receiver': self.receiver,
                               'payload': self.payload,
                               'signature': self.signature,
                               'pub_key': self.pub_key,
                               'nonce': self.nonce})
        elif dump_format == 'json-raw':  # TODO: change to self.dump('bytes')
            return json.dumps({'tx_type': self.tx_type.value,
                               'sender': self.sender,
                               'receiver': self.receiver,
                               'payload': self.payload,
                               'signature': self.signature,
                               'pub_key': self.pub_key,
                               'nonce': self.nonce})
        else:
            raise NotImplementedError
