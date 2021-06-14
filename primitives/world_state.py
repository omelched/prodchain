from __future__ import annotations

import copy
from typing import Union

from crypto.hashing import dsha256, keccak_hash
from mpt import MerklePatriciaTrie
from primitives.accounts import Account
from primitives.assets import Asset, AssetOwnershipType, CREATE_ASSET, CURRENCY_ASSET, AssetStatus, UPDATE_ASSET
from primitives.transactions import Transaction
from primitives.world_state_modifications import WorldStateModificationType


class WorldState(object):
    _accounts_trie: MerklePatriciaTrie = None
    _accounts_storage: dict[bytes, bytes] = {}
    _accounts: dict[bytes, Account] = {}
    _assets_trie: MerklePatriciaTrie = None
    _assets_storage: dict[bytes, bytes] = {}
    _assets: dict[bytes, Asset] = {}

    @property
    def state_roots_hash(self):
        return dsha256(self._accounts_trie.root_hash().hex() + self._assets_trie.root_hash().hex())

    def __init__(self, storages: tuple[dict, dict] = None) -> None:
        if storages:
            self._accounts_storage = storages[0]
            self._assets_storage = storages[1]

        self._accounts_trie = MerklePatriciaTrie(self._accounts_storage)
        self._assets_trie = MerklePatriciaTrie(self._assets_storage)

    def _register_account_modification(self, account: Account) -> None:
        assert isinstance(account, Account)

        key = account.name.encode('utf-8')

        self._accounts_trie.update(key, account.root_hash)
        self._accounts[key] = account

    def _register_asset_modification(self, asset: Asset) -> None:
        assert isinstance(asset, Asset)

        key = asset.name.encode('utf-8')

        self._assets_trie.update(key, asset.state_hash)
        self._assets[key] = asset

    def account_exists(self, account_name: Union[str, bytes]) -> bool:
        if isinstance(account_name, str):
            account_name = account_name.encode('utf-8')
        return account_name in self._accounts

    def execute_tx(self, tx: Transaction) -> WorldState:
        """Executes tx against current state and returns modified copy.

        Deepcopies current state,
        atomizes tx in sequence of WorldStateModification and payload keywords,
        tries to execute them.

        :param tx: transaction to be executed
        :type tx: Transaction
        :return: world state
        :rtype: WorldState
        """
        _new_world_state = copy.deepcopy(self)  # FIXME: may eat the fuck up RAM eventualy

        instructions = tx.atomize()

        for instruction in instructions:
            try:
                _new_world_state._execute_state_modification(instruction[0], **instruction[1])
            except Exception:
                raise

        return _new_world_state

    def _execute_state_modification(self, modification: WorldStateModificationType, **kwargs) -> None:
        """Executes arbitrary state modification instruction on self state.

        :param author_name:
        :param modification:
        :param kwargs:
        :return:
        """
        # TODO: switch to Structural Pattern Matching as soon as python3.10 released
        if modification == WorldStateModificationType.add_asset_to_account:

            account_name = kwargs['account']
            assert isinstance(account_name, (str, bytes))
            if isinstance(account_name, str):
                account_name = account_name.encode('utf-8')

            asset_name = kwargs['asset']
            assert isinstance(asset_name, (str, bytes))
            if isinstance(asset_name, str):
                asset_name = asset_name.encode('utf-8')

            ownership_type = kwargs['ownership_type']
            assert isinstance(ownership_type, AssetOwnershipType)

            amount = kwargs['amount']
            assert isinstance(amount, int)

            try:
                account = self._accounts[account_name]
            except KeyError:
                account = Account(account_name)

            try:
                asset = self._assets[asset_name]
            except KeyError:
                raise

            assert asset.status in [AssetStatus.active]

            try:
                account.add_asset(asset, ownership_type, amount)
            except Exception:
                raise

            self._register_account_modification(account)

        elif modification == WorldStateModificationType.sub_asset_from_account:

            account_name = kwargs['account']
            assert isinstance(account_name, (str, bytes))
            if isinstance(account_name, str):
                account_name = account_name.encode('utf-8')

            asset_name = kwargs['asset']
            assert isinstance(asset_name, (str, bytes))
            if isinstance(asset_name, str):
                asset_name = asset_name.encode('utf-8')

            ownership_type = kwargs['ownership_type']
            assert isinstance(ownership_type, AssetOwnershipType)

            amount = kwargs['amount']
            assert isinstance(amount, int)

            try:
                account = self._accounts[account_name]
            except KeyError:
                raise

            try:
                asset = self._assets[asset_name]
            except KeyError:
                raise

            assert asset.status in [AssetStatus.active]

            try:
                account.sub_asset(asset, ownership_type, amount)
            except Exception:
                raise

            self._register_account_modification(account)

        elif modification == WorldStateModificationType.create_asset:
            # assert all(k in ('name', 'type', 'status') for k in kwargs)
            # if not height == 0:
            #     try:
            #         author = self._accounts[author_name.encode('utf-8')]
            #     except KeyError:
            #         raise
            #
            #     assert author.check_asset(CREATE_ASSET, AssetOwnershipType.owner)
            #
            #     asset = Asset(kwargs['name'], kwargs['type'], kwargs['active'])
            #
            #     self._register_asset_modification(asset)
            #
            # else:
            #     asset = Asset(kwargs['name'], kwargs['type'], kwargs['active'])
            #
            #     self._register_asset_modification(asset)
            raise NotImplementedError

        elif modification == WorldStateModificationType.update_asset:
            raise NotImplementedError
        else:
            raise RuntimeError

    def execute_reward_modification(self, beneficiary: Union[str, bytes], amount: int) -> None:
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

    def prepare_for_genesis(self, me: str) -> None:

        self._register_asset_modification(CURRENCY_ASSET)
        self._register_asset_modification(CREATE_ASSET)
        self._register_asset_modification(UPDATE_ASSET)
        self._execute_state_modification(WorldStateModificationType.add_asset_to_account,
                                         account=me,
                                         asset=CREATE_ASSET.name,
                                         ownership_type=AssetOwnershipType.owner,
                                         amount=1)
        self._execute_state_modification(WorldStateModificationType.add_asset_to_account,
                                         account=me,
                                         asset=UPDATE_ASSET.name,
                                         ownership_type=AssetOwnershipType.owner,
                                         amount=1)
