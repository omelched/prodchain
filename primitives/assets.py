from enum import Enum
from crypto.hashing import dsha256


class AssetType(Enum):
    fungible = 0x00
    nonfungible = 0x01

    @property
    def value(self):
        return self._value_.to_bytes(1, 'big').hex()


class AssetOwnershipType(Enum):
    owner = 0x00
    comission = 0x01
    agent = 0x02

    @property
    def value(self):
        return self._value_.to_bytes(1, 'big').hex()


class Asset(object):
    name: str = None
    type: AssetType = None
    active: bool = True

    @property
    def state_hash(self):
        return dsha256(self.name + self.type.value + self.active.to_bytes(1, 'big').hex())

    def __init__(self, name: str, _type: AssetType, active: bool):
        self.name = name
        self.type = _type
        self.active = active


# predefined Assets for _assets_trie

CREATE_ASSET = Asset('0' * 64, AssetType.nonfungible, True)
UPDATE_ASSET = Asset('0' * 63 + '1', AssetType.nonfungible, True)
DELETE_ASSET = Asset('0' * 63 + '2', AssetType.nonfungible, True)
CURRENCY_ASSET = Asset('f' * 64, AssetType.fungible, True)
