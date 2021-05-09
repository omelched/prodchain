from typing import Union

from crypto.hashing import dsha256
from mpt import MerklePatriciaTrie
from primitives.assets import Asset, AssetOwnershipType, AssetType


class Account(object):
    name: str = ''
    _storage: dict[bytes, bytes] = {}
    _trie: MerklePatriciaTrie = None

    @property
    def root_hash(self):
        return self._trie.root_hash()

    def __init__(self, name: Union[str, bytes], storage: dict = None):
        assert isinstance(name, (str, bytes))
        if isinstance(name, bytes):
            name = name.hex()
        self.name = name
        if storage:
            self._storage = storage

        self._trie = MerklePatriciaTrie(self._storage)

    def add_asset(self, asset: Asset, ownership_type: AssetOwnershipType, amount: int):
        assert isinstance(asset, Asset)
        assert isinstance(ownership_type, AssetOwnershipType)

        key = dsha256(asset.name + ownership_type.value).encode('utf-8')

        try:
            prev_value = int.from_bytes(self._trie.get(key), 'big')
        except KeyError:
            prev_value = 0

        value = prev_value + amount
        assert not (asset.type == AssetType.nonfungible and value != 1)
        assert value >= 1

        self._trie.update(key, value.to_bytes(32, 'big'))

    def sub_asset(self, asset: Asset, ownership_type: AssetOwnershipType, amount: int):
        assert isinstance(asset, Asset)
        assert isinstance(ownership_type, AssetOwnershipType)

        key = dsha256(asset.name + ownership_type.value).encode('utf-8')

        try:
            prev_value = int.from_bytes(self._trie.get(key), 'big')
        except KeyError:
            raise

        value = prev_value + amount
        if value == 0:
            self._trie.delete(key)
            return

        assert not (asset.type == AssetType.nonfungible)
        self._trie.update(key, value.to_bytes(32, 'big'))

    def check_asset(self, asset: Asset, ownership_type: AssetOwnershipType, amount: int = 1):
        assert isinstance(asset, Asset)
        assert isinstance(ownership_type, AssetOwnershipType)

        key = dsha256(asset.name + ownership_type.value).encode('utf-8')

        try:
            value = int.from_bytes(self._trie.get(key), 'big')
        except KeyError:
            return False

        if value >= amount:
            return True

        return False

    def check_pubk(self, pubk: str):
        return dsha256(pubk) == self.name
