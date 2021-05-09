from primitives.blocks import Block, BlockHeader
from primitives.assets import CURRENCY_ASSET, CREATE_ASSET, DELETE_ASSET, UPDATE_ASSET, AssetOwnershipType
from primitives.world_state import WorldState, WorldStateModification

import datetime

me = '82be969bdeb6216e89a0e80fdf0c93c2e64b120af0b50abd3d9f6d4a09b395cd'


class BlockChain(object):
    chain: list = []
    _state: WorldState = None

    @property
    def last(self):
        return self.chain[-1]

    def __init__(self):
        self._state = WorldState()
        self._add_genesis_block()

    def _add_genesis_block(self):
        transactions = []
        self._state.execute_state_modification(0, '',
                                               WorldStateModification.create_asset,
                                               name=CURRENCY_ASSET.name,
                                               type=CURRENCY_ASSET.type,
                                               active=CURRENCY_ASSET.active)
        self._state.execute_state_modification(0, '',
                                               WorldStateModification.create_asset,
                                               name=CREATE_ASSET.name,
                                               type=CREATE_ASSET.type,
                                               active=CREATE_ASSET.active)
        self._state.execute_state_modification(0, '',
                                               WorldStateModification.create_asset,
                                               name=UPDATE_ASSET.name,
                                               type=UPDATE_ASSET.type,
                                               active=UPDATE_ASSET.active)
        self._state.execute_state_modification(0, '',
                                               WorldStateModification.create_asset,
                                               name=DELETE_ASSET.name,
                                               type=DELETE_ASSET.type,
                                               active=DELETE_ASSET.active)
        self._state.execute_state_modification(0, '',
                                               WorldStateModification.add_asset_to_account,
                                               account_name=me,
                                               asset=CREATE_ASSET,
                                               ownership_type=AssetOwnershipType.owner,
                                               amount=1)
        self._state.execute_state_modification(0, '',
                                               WorldStateModification.add_asset_to_account,
                                               account_name=me,
                                               asset=UPDATE_ASSET,
                                               ownership_type=AssetOwnershipType.owner,
                                               amount=1)
        self._state.execute_state_modification(0, '',
                                               WorldStateModification.add_asset_to_account,
                                               account_name=me,
                                               asset=DELETE_ASSET,
                                               ownership_type=AssetOwnershipType.owner,
                                               amount=1)

        gb = Block(
            BlockHeader(
                parent_hash='0' * 64,
                beneficiary=me,
                target=110427941548649020598956093796432407239217743554726184882600387580788735,
                height=0,
                timestamp=datetime.datetime.utcnow(),
                state_root=self._state.root_hash,
                comment='init'
            ),
            transactions
        )
        gb.mine()
        self.add_block(gb)
        print(gb.hash)

    def add_block(self, new_block: Block):
        assert isinstance(new_block, Block)
        assert new_block.valid
        self.chain.append(new_block)
