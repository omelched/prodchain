import datetime
import json

from primitives.transactions import Transaction
from crypto.hashing import dsha256, keccak_hash


class BlockHeader(object):
    parent_hash: str = ''
    beneficiary: str = ''
    state_root_hash: str = ''
    tx_root_hash: str = ''
    target: int = 0
    heigth: int = 0
    timestamp: datetime.datetime = datetime.datetime.utcnow()
    comment: str = ''
    nonce: int = 0

    @property
    def hash(self):
        return dsha256(self.dump('json_raw'))

    def __init__(self, parent_hash: str, beneficiary: str, target: int, height: int, timestamp: datetime.datetime,
                 state_root: str = None, tx_root: str = None, comment: str = None, nonce: int = None):

        self.parent_hash = parent_hash
        self.beneficiary = beneficiary
        self.target = target
        self.heigth = height
        self.timestamp = timestamp.astimezone(datetime.timezone.utc).replace(microsecond=0)
        if state_root:
            self.state_root_hash = state_root
        if tx_root:
            self.tx_root_hash = tx_root
        if comment:
            self.comment = comment
        if nonce:
            self.nonce = nonce

        assert self.target <= int('0x000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF', 16)

    def __repr__(self):
        return f'{type(self).__name__}({self.parent_hash}, {self.beneficiary}, {self.target}, {self.heigth},' \
               f'{self.timestamp}, {self.state_root_hash}, {self.tx_root_hash}, {self.comment}, {self.nonce})'

    @staticmethod
    def json_parser_hook(dump: dict):
        assert all(k in dump for k in ('parent_hash', 'beneficiary', 'target', 'height', 'timestamp'))

        more_args = {}
        for arg in ('state_root', 'tx_root', 'comment', 'nonce'):
            try:
                value = dump['state_root']
            except KeyError:
                value = None
            more_args[arg] = value

        return BlockHeader(dump['parent_hash'],
                           dump['beneficiary'],
                           dump['target'],
                           dump['height'],
                           datetime.datetime.fromtimestamp(dump['timestamp']),
                           state_root=more_args['state_root'],
                           tx_root=more_args['tx_root'],
                           comment=more_args['comment'],
                           nonce=more_args['nonce'])

    def dump(self, dump_format: str = 'json'):
        if dump_format == 'json':
            return json.dumps({
                'hash': self.hash,
                'parent_hash': self.parent_hash,
                'beneficiary': self.beneficiary,
                'target': self.target,
                'height': self.heigth,
                'timestamp': int(self.timestamp.timestamp()),
                'state_root': self.state_root_hash,
                'tx_root': self.tx_root_hash,
                'comment': self.comment,
                'nonce': self.nonce
            })
        elif dump_format == 'json_raw':  # TODO: replace by bytes-like dump
            return json.dumps({
                'parent_hash': self.parent_hash,
                'beneficiary': self.beneficiary,
                'target': self.target,
                'height': self.heigth,
                'timestamp': int(self.timestamp.timestamp()),
                'state_root': self.state_root_hash,
                'tx_root': self.tx_root_hash,
                'comment': self.comment,
                'nonce': self.nonce
            })
        else:
            raise NotImplementedError


class Block(object):
    header: BlockHeader
    transactions: list[Transaction]

    @property
    def hash(self):
        return self.header.hash

    @property
    def tx_root(self):
        return self._compute_tx_merkle_root(self.transactions)

    def mine(self):
        while int(self.hash, 16) > self.header.target:
            self.header.nonce = self.header.nonce + 1

    @staticmethod
    def _compute_tx_merkle_root(txs: list[Transaction]) -> str:
        def compute_merkle_nodes(_hashes: list[str]) -> list[str]:
            if not len(_hashes) % 2:
                _hashes.append(_hashes[-1])
            _hashes = [dsha256(i[0] + i[1]) for i in zip([v for i, v in enumerate(_hashes) if not i % 2],
                                                         [v for i, v in enumerate(_hashes) if i % 2])]
            return _hashes

        if not txs:
            return '0' * 64

        hashes = [tx.hash for tx in txs]
        while len(hashes) != 1:
            hashes = compute_merkle_nodes(hashes)

        return hashes[0]

    def __init__(self, header: BlockHeader, transactions: list[Transaction]):
        assert isinstance(header, BlockHeader)
        assert all(isinstance(tx, Transaction) for tx in transactions)

        self.header = header
        self.transactions = transactions

        if self.header.tx_root_hash:
            assert self.header.tx_root_hash == self.tx_root
        else:
            self.header.tx_root_hash = self.tx_root

    def __repr__(self):
        return f'{type(self).__name__}({self.header}, {len(self.transactions)} txs)'

    @staticmethod
    def json_parser_hook(dump: dict):
        assert all(k in dump for k in ('hash', 'header', 'transactions'))

        _txs = []
        for tx in dump['transactions']:
            _txs.append(json.loads(tx, object_hook=Transaction.json_parser_hook))
        _header = json.loads(dump['header'], object_hook=BlockHeader.json_parser_hook)

        block = Block(_header, _txs)
        assert block.hash == dump['hash']
        return block

    def dump(self, dump_format: str = 'json'):
        if dump_format == 'json':
            return json.dumps({'hash': self.hash,
                               'header': self.header.dump(),
                               'transactions': [tx.dump() for tx in self.transactions]})
        else:
            raise NotImplementedError
