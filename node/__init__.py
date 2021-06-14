from typing import Callable, Union, Optional
from datetime import datetime

from flask import Flask

from utils import config, logger
from primitives import Transaction, BlockChain, Block, BlockHeader


class CallbackTrigger(object):
    name: str = ''
    active: bool = False
    callback: Callable = None


class Node(Flask):
    tx_pool: list[Transaction] = []
    blockchain: BlockChain = None
    _triggers: list[CallbackTrigger] = []
    _mined_block: Optional[Block] = None

    def __init__(self, import_name):
        super().__init__(import_name)

    def main_loop(self) -> None:
        """Starts main loop of node (mining + callback executions).

        :return: None
        :rtype: None
        """

        _exit_loop = False

        while not _exit_loop:

            self._mine()

            for call in self._callbacks_to_execute():
                call()  # TODO: pass arbitrary variables from Callback

    def _callbacks_to_execute(self) -> Union[tuple[Callable, ...], tuple[()]]:
        """Returns callbacks to be executed.

        :return: Tuple of callables which need to be executed.
        :rtype: tuple[Callable]
        """
        return tuple(t.callback for t in self._triggers if t.active)

    def _mine(self):

        if not self._mined_block:

            txs = self.tx_pool[:]

            try:
                new_state = self.blockchain.validate_txs_on_current_state(txs)
            except Exception:
                raise

            self._mined_block = Block(
                BlockHeader(
                    parent_hash=self.blockchain.last.hash,
                    beneficiary='82be969bdeb6216e89a0e80fdf0c93c2e64b120af0b50abd3d9f6d4a09b395cd',
                    target=28269553036454149273332760011886696253239742350009903329945699220681916415,
                    height=self.blockchain.height,
                    timestamp=datetime.now(),
                    state_root=new_state.state_roots_hash,
                    comment=f'test height {self.blockchain.height}'
                ),
                self.tx_pool
            )

            self._mined_block.mine()  # TODO: multiprocessing

            self.blockchain.add_block(self._mined_block)
            self._mined_block = None

        ...


server = Node(__name__)
server.config.from_object(config)
logger.info('OK')

import node.rpc  # noqa
