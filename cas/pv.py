# -*- coding: utf-8 -*-

import logging

log=logging.getLogger('cas.pv')

from defs import *
from cadata import caValue
from error import CAError, ECA_NOCONVERT

class PV(object):
    
    def __init__(self, name, dbf, maxcount):
        self._name=name
        self.dbf=dbf
        self.maxcount=maxcount
        
        self.channels=set()

    @property
    def name(self):
        return self._name

    def info(self, channel):
        return (self.dbf, self.maxcount)

    def rights(self, channel):
        return 3

    def connect(self, channel):
        self.channels.add(channel)

    def disconnect(self, channel):
        self.channels.remove(channel)

    def get(self, channel, dtype, count):
        return None

    def set(self, channel, data, dtype, count):
        return False

    def monitor(self, channel, dtype, count, mask):
        return self.get(channel, dtype, count)

    def post(self,mask):
        for c in self.channels:
            c.post(mask)

    def __str__(self):
        return 'PV %(name)s with %(maxcount)d of %(dtype)d'%self.__dict__

class BasicPV(PV):
    def __init__(self, name, dtype, value=None, maxcount=None):
        import time
        if maxcount is None:
            maxcount=len(value)
        PV.__init__(self, name, dtype , maxcount)
        self.data=caValue(dtype)
        if value is not None:
            self.data.value=value
            self.data.stamp=time.time()

    def get(self, channel, dtype, count):
        dbf, meta = dbr_to_dbf(dtype)
        if dbf!=self.dbf:
            raise CAError("Unsupported type conversion", ECA_NOCONVERT)
        return self.data.tostring(dtype, count)

    def set(self, channel, data, dtype, count):
        dbf, meta = dbr_to_dbf(dtype)
        if dbf!=self.dbf:
            log.error("trying to assign %d to %d",dbf,self.dbf)
            raise CAError("Unsupported type conversion", ECA_NOCONVERT)

        log.info('set %s to %s',self.name,repr(data))
        self.data.fromstring(data, dtype, count)
        self.post(DBE_VALUE|DBE_LOG)
        return True

