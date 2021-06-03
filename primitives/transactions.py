from enum import Enum
from typing import Union
import json

from crypto.hashing import dsha256
from primitives.world_state_modifications import WorldStateModificationType
from primitives.assets import AssetOwnershipType


class TransactionTypes(Enum):
    # simple transfer
    transfer = '00'

    # transfer with confirmation
    transfer_with_confirmation = '10'
    confirm_transfer = '11'
    reject_transfer = '12'
    cancel_transfer = '13'

    # asset creation
    create_as_import = '20'

    # asset modification
    create_asset = 'f0'
    delete_asset = 'f1'
    update_asset = 'f2'

    def payload_is_valid(self, payload):
        # TODO: switch to Structural Pattern Matching as soon as python3.10 released
        if self.value in ['00', '11']:  # transfer
            return all(k in payload for k in ['asset', 'amount'])
        else:
            raise NotImplementedError


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

    def __repr__(self):
        return f'{type(self).__name__}({self.tx_type.value}, {self.sender}, {self.receiver}, {self.payload},' \
               f'{self.signature}, {self.pub_key}, {self.nonce})'

    @staticmethod
    def json_parser_hook(dump: dict):
        assert all(k in dump for k in ('hash', 'tx_type', 'sender', 'receiver',
                                       'payload', 'signature', 'pub_key', 'nonce'))

        tx = Transaction(
            TransactionTypes(int(dump['tx_type'], 16)),
            dump['sender'],
            dump['reciever'],
            json.loads(dump['payload']),
            dump['signature'],
            dump['pub_key'],
            dump['nonce']
        )

        assert tx.hash == dump['hash']

        return tx

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

    def atomize(self) -> tuple[tuple[WorldStateModificationType, dict[str, Union[str, int]]], ...]:
        """Split transaction into sequence of world state modification types, and key-value dict to execute em'.


        # TODO: switch to Structural Pattern Matching as soon as python3.10 released

        :return: tuple of modifications types and values to execute them
        :rtype: ttuple[tuple[WorldStateModificationType, dict[str, Union[str, int]]], ...]
        """
        if self.tx_type.name == TransactionTypes.transfer.name:
            assert all(k in ('recipient', 'asset', 'ownership_type', 'amount') for k in self.payload)
            return (
                (
                    WorldStateModificationType.sub_asset_from_account,
                    {
                        'account': self.sender,
                        'asset': self.payload['asset'],
                        'ownership_type': AssetOwnershipType(self.payload['ownership_type']),
                        'amount': self.payload['amount']
                    }
                ),
                (
                    WorldStateModificationType.add_asset_to_account,
                    {
                        'account': self.payload['recipient'],
                        'asset': self.payload['asset'],
                        'ownership_type': AssetOwnershipType(self.payload['ownership_type']),
                        'amount': self.payload['amount']
                    }
                )
            )
        else:
            raise NotImplementedError
