from enum import Enum
from typing import Union

from crypto.hashing import dsha256
from mpt import MerklePatriciaTrie
from primitives.accounts import Account
from primitives.assets import Asset, AssetOwnershipType, CREATE_ASSET, CURRENCY_ASSET


class WorldStateModification(Enum):
    add_asset_to_account = 0x00
    sub_asset_from_account = 0x01
    create_asset = 0xf0
    delete_asset = 0xf1
    update_asset = 0xf2


class WorldState(object):
    _accounts_trie: MerklePatriciaTrie = None
    _accounts_storage: dict[bytes, bytes] = {}
    _accounts: dict[bytes, Account] = {}
    _assets_trie: MerklePatriciaTrie = None
    _assets_storage: dict[bytes, bytes] = {}
    _assets: dict[bytes, Asset] = {}

    @property
    def root_hash(self):
        return dsha256(self._accounts_trie.root_hash().hex() + self._assets_trie.root_hash().hex())

    def __init__(self, storages: tuple[dict, dict] = None):
        if storages:
            self._accounts_storage = storages[0]
            self._assets_storage = storages[1]

        self._accounts_trie = MerklePatriciaTrie(self._accounts_storage)
        self._assets_trie = MerklePatriciaTrie(self._assets_storage)
        self._default_state()

    def _default_state(self):
        ...

    def _register_account_modification(self, account: Account):
        assert isinstance(account, Account)

        key = account.name.encode('utf-8')

        self._accounts_trie.update(key, account.root_hash)
        self._accounts[key] = account

    def _register_asset_modification(self, asset: Asset):
        assert isinstance(asset, Asset)

        key = asset.name.encode('utf-8')

        self._assets_trie.update(key, asset.state_hash)
        self._assets[key] = asset

    def _register_asset_deletion(self, asset: Asset):
        assert isinstance(asset, Asset)

        key = asset.name.encode('utf-8')

        self._assets_trie.delete(key)
        del self._assets[key]

    def execute_state_modification(self, height: int, author_name: str, modification: WorldStateModification, **kwargs):
        # TODO: switch to Structural Pattern Matching as soon as python3.10 released
        if modification == WorldStateModification.add_asset_to_account:
            assert all(k in ('account_name', 'asset', 'ownership_type', 'amount') for k in kwargs)

            account_name = kwargs['account_name']
            assert isinstance(account_name, (str, bytes))
            if isinstance(account_name, str):
                account_name.encode('utf-8')

            asset = kwargs['asset']
            assert isinstance(asset, Asset)

            ownership_type = kwargs['ownership_type']
            assert isinstance(ownership_type, AssetOwnershipType)

            amount = kwargs['amount']
            assert isinstance(amount, int)

            try:
                account = self._accounts[account_name]
            except KeyError:
                account = Account(account_name)

            try:
                account.add_asset(asset, ownership_type, amount)
            except Exception:
                raise

            self._register_account_modification(account)

        elif modification == WorldStateModification.sub_asset_from_account:
            assert all(k in ('account_name', 'asset', 'ownership_type', 'amount') for k in kwargs)

            account_name = kwargs['account_name']
            assert isinstance(account_name, (str, bytes))
            if isinstance(account_name, str):
                account_name.encode('utf-8')

            asset = kwargs['asset']
            assert isinstance(asset, Asset)

            ownership_type = kwargs['ownership_type']
            assert isinstance(ownership_type, AssetOwnershipType)

            amount = kwargs['amount']
            assert isinstance(amount, int)

            try:
                account = self._accounts[account_name]
            except KeyError:
                raise

            try:
                account.sub_asset(asset, ownership_type, amount)
            except Exception:
                raise

            self._register_account_modification(account)

        elif modification == WorldStateModification.create_asset:
            assert all(k in ('name', 'type', 'active') for k in kwargs)
            if not height == 0:
                try:
                    author = self._accounts[author_name.encode('utf-8')]
                except KeyError:
                    raise

                assert author.check_asset(CREATE_ASSET, AssetOwnershipType.owner)

                asset = Asset(kwargs['name'], kwargs['type'], kwargs['active'])

                self._register_asset_modification(asset)

            else:
                asset = Asset(kwargs['name'], kwargs['type'], kwargs['active'])

                self._register_asset_modification(asset)

        elif modification == WorldStateModification.update_asset:
            raise NotImplementedError
        elif modification == WorldStateModification.delete_asset:
            raise NotImplementedError
        else:
            raise RuntimeError

    def execute_reward_modification(self, beneficiary: Union[str, bytes], amount: int):
        assert isinstance(beneficiary, (str, bytes))
        if isinstance(beneficiary, str):
            beneficiary.encode('utf-8')

        try:
            account = self._accounts[beneficiary]
        except KeyError:
            account = Account(beneficiary)

        asset = CURRENCY_ASSET

        try:
            account.add_asset(asset, AssetOwnershipType.owner, amount)
        except Exception:
            raise

        self._register_account_modification(account)

