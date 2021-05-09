import json

from .operations import ScriptOperation, OPS
from .stacks import Stack, ConditionalStack


class Script(object):
    ops: list

    def __init__(self, ops: list):
        self.ops = ops

    def __add__(self, other):
        assert isinstance(other, type(self))
        return Script(self.ops + other.ops)

    def __repr__(self):
        return f'{type(self).__name__}({self.ops})'

    @staticmethod
    def json_parser_hook(dump: dict):
        assert 'ops' in dump
        _ops = []
        for op in dump['ops']:
            if op in OPS:
                _ops.append(OPS[op])
            else:
                _ops.append(op)

        return Script(_ops)

    def dump(self, dump_format: str = 'json'):
        if dump_format == 'json':
            return json.dumps({'ops': [op.name if issubclass(op, ScriptOperation) else op for op in self.ops]})
        else:
            raise NotImplementedError


class ScriptExecutor(object):
    prev_tx_hash: str
    script: Script
    stack: Stack
    c_stack: ConditionalStack

    def __init__(self, prev_tx_hash: str, unlock_script: Script, lock_script: Script):
        self.script = unlock_script + lock_script
        self.stack = Stack()
        self.c_stack = ConditionalStack()
        for op in self.script.ops:
            if issubclass(op, ScriptOperation):
                op.execute(self.stack, self.c_stack, prev_tx_hash)
            else:
                self.stack.append(op)
