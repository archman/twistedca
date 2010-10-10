# -*- coding: utf-8 -*-

import logging

log=logging.getLogger('cas.pv')

from util.defs import *
from util.cadata import caMetaProxy, tostring, fromstring
from util.error import CAError, ECA_NOCONVERT

class PV(object):
    
    def __init__(self, name, value, meta, maxcount=None):
        import time
        if maxcount is None:
            maxcount=len(value)
        self._name=name
        self._maxcount=maxcount
        
        self.channels=set()

        self.value=value
        self.meta=meta

    @property
    def name(self):
        return self._name

    @property
    def maxcount(self):
        return self._maxcount

    def info(self, channel):
        return (self.meta.dbf, self._maxcount)

    def rights(self, channel):
        return 3

    def connect(self, channel):
        self.channels.add(channel)

    def disconnect(self, channel):
        self.channels.remove(channel)

    def get(self, channel, dbr, count):
        try:
            return tostring(self.value, self.meta, dbr, count)
        except ValueError:
            # when no conversion is possible rsrv returns 0
            return tostring([0]*count, self.meta, dbr, count)

    def set(self, channel, data, dbr, count):

        try:
            val, rmeta = fromstring(data, dbr, count, self.meta)
        except ValueError:
            log.exception("type conversion failed")
            raise CAError("type conversion failed", ECA_NOCONVERT)
        log.info('set %s to %s',self.name,str(val))
        self.value=val
        self.post(DBE.VALUE|DBE.LOG)
        return True

    def monitor(self, channel, dtype, count, mask):
        return self.get(channel, dtype, count)

    def post(self,mask):
        for c in self.channels:
            c.post(mask)

    def __str__(self):
        vals={'dbf':self.meta.dbf}
        vals.update(self.__dict__)
        return 'PV %(_name)s with %(_maxcount)d of %(dbf)d'%vals
