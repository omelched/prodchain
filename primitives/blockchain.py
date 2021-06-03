import datetime
from typing import Union
import copy
from typing import Optional

from primitives.blocks import Block, BlockHeader, Transaction
from primitives.assets import CURRENCY_ASSET, CREATE_ASSET, UPDATE_ASSET, AssetOwnershipType
from primitives.world_state import WorldState, WorldStateModificationType
from crypto import dsha256, check_signature_ecdsa


class BlockChain(object):
    """Represents blockchain.

    Public attributes:
        chain — chain of blocks
        last — last block
    Private attributes:
        _state — current world state
    Public methods:
        add_block(...) — validates and adds new block to chain
    Private methods:
        _add_genesis_block(...) — adds first block to chain

    New blocks SHOULD BE added only with add_block(...).
    """
    chain: list[Block] = []
    _state: WorldState = None

    @property
    def last(self) -> Optional[Block]:
        """Returns last block in blockchain.

        :return: last block in chain
        :rtype: Block
        """
        try:
            return self.chain[-1]
        except IndexError:
            return None

    def __init__(self, chain: list[Block] = None, state: WorldState = None) -> None:
        """Initialization of blockchain.

        :param chain: list if blocks to initialize blockchain on (optional)
        :type chain: list[Block]
        :param state: world state to initialize blockchain on (optional)
        :type state: WorldState

        Initializes blockchain from existing world state and chain, checks that last block represents given world state
        and validates whole chain.
        If not provided, creates new blockchain, adds genesis block.
        """
        if not all((chain, state)):
            self._state = WorldState()
            self._add_genesis_block()
        else:
            assert isinstance(state, WorldState), TypeError
            assert state.root_hash == chain[-1].header.state_root_hash
            assert self._validate_chain(chain)

            self.chain = chain
            self._state = state

    def _add_genesis_block(self) -> None:
        """Adds genesis block to blockchain.

        Creates first assets (currency and some roles).

        :return: None
        """

        # for testing purpose
        me = '82be969bdeb6216e89a0e80fdf0c93c2e64b120af0b50abd3d9f6d4a09b395cd'

        transactions = []
        self._state.prepare_for_genesis(me)

        gb = Block(
            BlockHeader(
                parent_hash='0' * 64,
                beneficiary=me,  # FIXME: ...
                target=28269553036454149273332760011886696253239742350009903329945699220681916415,
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

    def add_block(self, new_block: Block) -> None:
        """ Validates block and adds to blockchain.

        :param new_block: block to be added in blockchain
        :type new_block: Block
        :return: None
        """
        assert isinstance(new_block, Block)
        try:
            new_state = self._validate_block(new_block, self.last, self._state)
        except Exception:
            raise

        self.chain.append(new_block)
        self._state = new_state

    @staticmethod
    def _validate_chain(chain: list[Block]):
        """Quickly validates chain.

        Checks next:
            - all items in chain are Blocks
            - first block is at height 0
            - every next block has block.height == prev_block.height + 1
            - every next block has block.header.parent_hash == prev_block.hash
            - every next block has block.header.timestamp > prev_block.header.timestamp
            - every next block has block.header.timestamp <= prev_block.header.timestamp + 10 min
            - every block has block.header.tx_root_hash == merkle_hash(block.transactions)
            - target check ... (not implemented) # TODO

        Does not validates transactions in block — just assumes that it is ok.

        :param chain: chain of blocks to be validated
        :type chain: list[Block]
        :return: None
        """
        header_pairs = tuple((it[1].header, chain[it[0]].header) for it in enumerate(chain[1:]))
        ten_minutes = datetime.timedelta(minutes=10)

        assert isinstance(chain, list)
        assert len(chain) > 1
        assert all((isinstance(i, Block) for i in chain))
        assert chain[0].header.heigth == 0
        assert all((pair[0].heigth - pair[1].heigth == 1 for pair in header_pairs))
        assert all((pair[0].parent_hash == pair[1].hash for pair in header_pairs))
        assert all((pair[0].timestamp > pair[1].timestamp for pair in header_pairs))
        assert all((pair[0].timestamp <= pair[1].timestamp + ten_minutes for pair in header_pairs))
        assert all(block.header.tx_root_hash == block.compute_tx_merkle_root() for block in chain)

    def _validate_block(self, block: Block, prev_block: Block, world_state: WorldState) -> WorldState:
        """Validates arbitraty block on some arbitraty parent block and arbitraty state of blockchain.

        Checks:
            - block.header.height > 1
            - block.header.height == prev_block.header.height - 1
            - block.header.parent_hash == prev_block.hash
            - block.header.timestamp > prev_block.header.timestamp
            - block.header.timestamp <= prev_block.header.timestamp + 10 min
            - target check ... (not implemented) # TODO
            - block.header.tx_root_hash == merkle_hash(block.transactions)
            - validate all txs <there all txs are executed and new state calculated>
            - state_after_txs.root_hash = block.header.root_hash

        :param block: block to be validated
        :type block: Block
        :param prev_block: parent_block of to-be-validated block
        :type prev_block: Block
        :param world_state: world state to be validated against
        :type world_state: WorldState

        :return: modified world state
        :rtype: WorldState
        """
        if not block.header.heigth == 0:
            assert block.header.heigth >= 1
            assert block.header.heigth == prev_block.header.heigth - 1
            assert block.header.parent_hash == prev_block.hash
            assert block.header.timestamp > prev_block.header.timestamp
            assert block.header.timestamp <= prev_block.header.timestamp + datetime.timedelta(minutes=10)
        assert block.header.tx_root_hash == block.compute_tx_merkle_root()

        try:
            new_state = self._validate_txs(block.transactions, world_state)
        except Exception:
            raise

        assert new_state.root_hash == block.header.state_root_hash
        new_state.execute_reward_modification(block.header.beneficiary, 500)

        return new_state

    @staticmethod
    def _validate_txs(txs: list[Transaction], world_state: WorldState) -> WorldState:
        """Validates sequence of transactions and calculates modified world state.

        Checks:
            - tx.sender is in world state account trie
            - tx.pubkey matches tx.sender
            - tx.signature is valid
            - tx.payload valid for used tx.type
            - state modification can be executed <there new state is trying to be calculated>

        Every next transaction will be validated on and will modify new world state.

        :param txs: list of Transactions
        :type txs: list[Transaction]
        :param world_state: world state first transaction to be validated against
        :type world_state: WorldState

        :return: modified world state
        :rtype: WorldState
        """

        def validate_tx(tx: Transaction, _state: WorldState) -> WorldState:
            """Validates arbitrary transaction on arbitrary state.

            Lookup docsting for _validate_txs(...)

            :param tx: Transaction to be validated
            :type tx: Transaction
            :param _state: world state to be cvalidated against
            :type _state: WorldState
            :return: modified world state
            :rtype: WorldState
            :raises: # TODO: document exceptions
            """
            assert _state.account_exists(tx.sender)
            assert dsha256(tx.pub_key) == tx.sender
            assert check_signature_ecdsa(tx.pub_key, tx.signature, tx.hash)
            assert tx.tx_type.payload_is_valid(tx.payload)
            assert ...

            try:
                _new_state = _state.execute_tx(tx)
            except Exception:
                raise

            return _new_state

        assert all(isinstance(tx, Transaction) for tx in txs)
        assert isinstance(world_state, WorldState)

        new_world_state = copy.deepcopy(world_state)
        for tx in txs:
            try:
                new_world_state = validate_tx(tx, new_world_state)
            except Exception:
                raise

        return new_world_state
