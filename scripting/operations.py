import sys
import inspect

from scripting.exceptions import ScriptingException
from scripting.stacks import ConditionalStack
from crypto.signatures import check_signature_ecdsa
from crypto.hashing import sha256ripemd160


class ScriptOperation(object):
    id_: int = None
    name: str = None

    @classmethod
    def execute(cls, stack: list, cond_stack: ConditionalStack, prev_tx_hash):
        if cls._check_conditional_stack(cond_stack):
            return cls._execute(stack, cond_stack, prev_tx_hash)
        return None

    @classmethod
    def _execute(cls, stack: list, cond_stack: ConditionalStack, prev_tx_hash: str):
        raise NotImplementedError

    @classmethod
    def hex_id(cls):
        return hex(cls.id_)

    @classmethod
    def _check_conditional_stack(cls, cond_stack: ConditionalStack):
        if cond_stack or (cls.name in ['IF', 'ELSE', 'ENDIF']):
            return True
        return False


class Dup(ScriptOperation):
    name = 'DUP'
    id_ = 1

    @classmethod
    def _execute(cls, stack: list, cond_stack: ConditionalStack, prev_tx_hash: str):
        x = stack[-1]
        stack.append(x)


class Hash160(ScriptOperation):
    name = 'HASH160'
    id_ = 2

    @classmethod
    def _execute(cls, stack: list, cond_stack: ConditionalStack, prev_tx_hash: str):
        x = stack.pop(-1)
        stack.append(sha256ripemd160(x))


class Equal(ScriptOperation):
    name = 'EQUAL'
    id_ = 3

    @classmethod
    def _execute(cls, stack: list, cond_stack: ConditionalStack, prev_tx_hash: str):
        assert len(stack) > 1, ScriptingException
        x_1 = stack.pop(-1)
        x_2 = stack.pop(-1)

        stack.append(0x1.to_bytes(0x1.bit_length(), 'little') if x_1 == x_2 else bytes(1))


class If(ScriptOperation):
    name = 'IF'
    id_ = 4

    @classmethod
    def _execute(cls, stack: list, cond_stack: ConditionalStack, prev_tx_hash: str):
        c_value = False

        if cond_stack:
            assert len(stack) > 0
            c_value = False if stack[-1] == bytes(1) else True

        cond_stack += c_value


class Else(ScriptOperation):
    name = 'ELSE'
    id_ = 5

    @classmethod
    def _execute(cls, stack: list, cond_stack: ConditionalStack, prev_tx_hash: str):
        assert not cond_stack.empty

        cond_stack.toggle_top()


class EndIf(ScriptOperation):
    name = 'ENDIF'
    id_ = 6

    @classmethod
    def _execute(cls, stack: list, cond_stack: ConditionalStack, prev_tx_hash: str):
        assert not cond_stack.empty

        cond_stack.pop_back()

        return None


class CheckSig(ScriptOperation):
    name = 'CHECKSIG'
    id_ = 6

    @classmethod
    def _execute(cls, stack: list, cond_stack: ConditionalStack, prev_tx_hash: str):
        assert len(stack) > 1
        x_1 = stack.pop(-1)
        x_2 = stack.pop(-1)

        stack.append(check_signature_ecdsa(x_1, x_2, prev_tx_hash))


class Rot(ScriptOperation):
    name = 'ROT'
    id_ = 7

    @classmethod
    def _execute(cls, stack: list, cond_stack: ConditionalStack, prev_tx_hash: str):
        assert len(stack) > 2
        stack.append(stack.pop(-3))


class Drop(ScriptOperation):
    name = 'DROP'
    id_ = 7

    @classmethod
    def _execute(cls, stack: list, cond_stack: ConditionalStack, prev_tx_hash: str):
        assert len(stack) > 1
        stack.pop(-1)


class DoubleDrop(ScriptOperation):
    name = '2DROP'
    id_ = 8

    @classmethod
    def _execute(cls, stack: list, cond_stack: ConditionalStack, prev_tx_hash: str):
        assert len(stack) > 1
        del stack[-2:]


class Or(ScriptOperation):
    name = 'OR'
    id_ = 9

    @classmethod
    def _execute(cls, stack: list, cond_stack: ConditionalStack, prev_tx_hash: str):
        assert len(stack) > 1
        x_1 = False if stack.pop(-1) == bytes(1) else True
        x_2 = False if stack.pop(-1) == bytes(1) else True

        stack.append(x_1 or x_2)


OPS = {cls[1].name: cls[1] for cls in inspect.getmembers(sys.modules[__name__], inspect.isclass)
       if cls[1].__module__ == 'scripting.operations'}
del OPS[None]

"""
0
0
1234
026cba6812cc3fe6a09f823c007efdfca1d56cfbbf0959bdff725377b54e0c103341e252119c2b2c5151c554c9d63c31
OP_DUP OP_HASH160 630b3961c085e2648a56f8a25fe31211b28f4f53 OP_EQUAL
OP_IF OP_CHECKSIG OP_ELSE OP_2DROP 0 OP_ENDIF
OP_ROT OP_ROT
OP_DUP OP_HASH160 630b3961c085e2648a56f8a25fe31211b28f4f53 OP_EQUAL
OP_IF OP_CHECKSIG OP_ELSE OP_2DROP 0 OP_ENDIF
OP_OR
"""
