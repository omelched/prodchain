from typing import Union

from crypto.hashing import dsha256
from mpt import MerklePatriciaTrie
from primitives.assets import Asset, AssetOwnershipType, AssetType


class Account(object):
    """Represents unique account on blockchain which can own assets or/and send transactions to network.

    Public attributes:
        name — account unique identifier
        root_hash — account state hash
    Private attributes:
        _storage — key-value storage for _trie
        _trie — account state in Merkle Patricia trie
    Methods:
        add_asset(...) - add arbitrary asset of arbitrary value to account
        sub_asset(...) - substract arbitrary asset of arbitrary value from account
        check_asset(...) - check if amount of arbitrary asset on account >= arbitrary amount

    Account state is represented by keyword structure dsha256('asset.name' + 'ownership_type'): 'value'(int)
    and encoded in merkle patricia
    trie.
    Account state SHOULD BE modified only with class methods.
    """
    name: str = ''
    _storage: dict[bytes, bytes] = {}
    _trie: MerklePatriciaTrie = None

    @property
    def root_hash(self) -> bytes:
        """Computes and returns hash of current account state root.

        Unique (in respect to collisions) for every possible account state.

        :return: hash of current account state root
        :rtype: bytes
        """
        return self._trie.root_hash()

    def __init__(self, name: Union[str, bytes], storage: dict = None) -> None:
        """Initialization of object.

        Basic type assertions. If storage is undefined — assume is is a new account.

        :param name: name of account
        :type name: Union[str, bytes]
        :param storage: storage for Merkle Patricia trie (if exists)
        :type storage: dict
        """
        assert isinstance(name, (str, bytes))
        if isinstance(name, bytes):
            name = name.decode('utf-8')
        self.name = name
        if storage:
            self._storage = storage

        self._trie = MerklePatriciaTrie(self._storage)

    def add_asset(self, asset: Asset, ownership_type: AssetOwnershipType, amount: int) -> None:
        """Adds arbitrary asset of arbitrary value to account.

        Typing assertions and assertions that boolean asset may have value only in (0, 1).
        Asset must be in active state.

        :param asset: arbitrary asset to be added
        :type asset: Asset
        :param ownership_type: selected ownership type for asset
        :type ownership_type: AssetOwnershipType
        :param amount: arbitraty ammount to be added
        :type amount: int
        """
        assert isinstance(asset, Asset)
        assert isinstance(ownership_type, AssetOwnershipType)

        key = dsha256(asset.name + ownership_type.value).encode('utf-8')

        try:
            prev_value = int.from_bytes(self._trie.get(key), 'big')
        except KeyError:
            prev_value = 0

        value = prev_value + amount
        assert not (asset.type == AssetType.boolean and value != 1)
        assert value >= 1

        self._trie.update(key, value.to_bytes(32, 'big'))

    def sub_asset(self, asset: Asset, ownership_type: AssetOwnershipType, amount: int):
        """Substracts arbitrary asset of arbitrary value from account.

        Typing assertions and assertions that value may not be < 0.

        :param asset: arbitrary asset to be substracted
        :type asset: Asset
        :param ownership_type: selected ownership type for asset
        :type ownership_type: AssetOwnershipType
        :param amount: arbitraty ammount to be substracted
        :type amount: int
        """
        assert isinstance(asset, Asset)
        assert isinstance(ownership_type, AssetOwnershipType)

        key = dsha256(asset.name + ownership_type.value).encode('utf-8')

        if not self.check_asset(asset, ownership_type, amount):
            raise

        prev_value = int.from_bytes(self._trie.get(key), 'big')

        value = prev_value - amount
        if value == 0:
            self._trie.delete(key)
            return

        assert not (asset.type == AssetType.boolean)
        self._trie.update(key, value.to_bytes(32, 'big'))

    def check_asset(self, asset: Asset, ownership_type: AssetOwnershipType, amount: int = 1) -> bool:
        """Checks if amount of arbitrary asset on account >= arbitrary amount.

        Typing assertions.

        :param asset: arbitrary asset to be checked
        :type asset: Asset
        :param ownership_type: selected ownership type for asset
        :type ownership_type: AssetOwnershipType
        :param amount: arbitraty ammount to be checked
        :type amount: int
        :returns: True if value on account is sufficient for 'amount'. False if not.
        :rtype: bool
        """
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

