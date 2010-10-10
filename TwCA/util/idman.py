# -*- coding: utf-8 -*-


class IDManager(dict):
    """
    A dictionary with automatic key generation.
    implicit overwriting is disallowed
    """
    def __init__(self):
        self._next=0

    def add(self, holder):
        id=self._next
        self[id]=holder
        self._next+=1
        while self._next is self:
            self._next+=1
        return id

    def __setitem__(self, k, v):
        if k in self and v is not self[k]:
            raise KeyError("Key already in use")
        return dict.__setitem__(self,k,v)
