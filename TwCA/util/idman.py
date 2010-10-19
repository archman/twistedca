# -*- coding: utf-8 -*-

"""A variety of containers which are more aware of their contents
"""

class IDManager(dict):
    """
    A dictionary with automatic key generation.
    implicit overwriting is disallowed
    """
    def __init__(self):
        dict.__init__(self)
        self._next=0

    def add(self, holder):
        id=self._next
        self[id]=holder
        self._next+=1
        while self._next in self:
            self._next+=1
        return id

    def remove(self, id):
        self.pop(id, None)

    def __setitem__(self, k, v):
        if k in self and v is not self[k]:
            raise KeyError("Key already in use")
        return dict.__setitem__(self,k,v)

class CBManager(dict):
    """
    Keep a list of callbacks with optional arguments
    """
    
    def add(self, cb, *args, **kwargs):
        assert cb not in self
        self[cb]=(args,kwargs)

    def remove(self, cb):
        assert cb in self
        self.pop(cb)

    def __call__(self, *args, **kwargs):
        from copy import copy
        for cb,(a,kw) in self.iteritems():
            k=kwargs.copy()
            k.update(kw)
            cb(*(args+a), **k)

class DeferredManager(set):
    """Keep a set of Deferreds to fire.
    
    Each requester gets a new Deferred so that
    it can be chained by its user
    """
    __done=None

    def add(self,defer):
        raise NotImplementedError("Can't not add Deferreds manually")

    def _cancel(self, d):
        if d not in self:
            raise RuntimeError('Deferred already cancelled')
        self.remove(d)

    def get(self):
        d=self._get()
        d.cancel=lambda: self._cancel(d)
        return d

    def _get(self):
        from twisted.internet.defer import Deferred, \
                                           succeed, fail
        if self.__done is True:
            return succeed(self.__result)
        elif self.__done is False:
            return fail(self.__fail)

        d=Deferred()
        set.add(self, d)
        return d

    def callback(self, result):
        if self.__done:
            from twisted.internet.defer import AlreadyCalledError
            raise self.AlreadyCalledError('DeferredManager already run')

        self.__result=result
        self.__done=True
        for d in self:
            d.callback(result)

        self.clear()

    def errback(self, fail=None):
        if self.__done:
            from twisted.internet.defer import AlreadyCalledError
            raise self.AlreadyCalledError('DeferredManager already run')
        
        from twisted.python.failure import Failure

        self.__fail=fail
        self.__done=False
        if not isinstance(fail, Failure):
            fail = self.__fail = Failure(fail)
        for d in self:
            d.errback(fail)

        self.clear()

