from typing import Union


class Stack(list):
    pass


class ConditionalStack(object):
    """
    Shotout to github.com/bitcoin/bitcoin/blob/480bf01c295527bd212964efe4df3bb886db5654/src/script/interpreter.cpp#L297
    """
    _size: int = 0
    _first_false_pos: Union[int, None] = None

    @property
    def empty(self):

        return self._size == 0

    def __bool__(self):

        return self._first_false_pos is None

    def __add__(self, other):

        other = bool(other)

        if (self._first_false_pos is None) and (not other):
            self._first_false_pos = self._size
        self._size += 1

    def pop_back(self):

        assert self._size > 0

        self._size -= 1
        if self._first_false_pos == self._size:
            self._first_false_pos = None

    def toggle_top(self):

        assert self._size > 0

        if self._first_false_pos is None:
            self._first_false_pos = self._size - 1
        elif self._first_false_pos == self._size - 1:
            self._first_false_pos = None
        else:
            pass
