# -*- coding: utf-8 -*-

from defs import *
from cadata import caValue
from error import CAError

class PV(object):
    
    def __init__(self, name, dtype, maxcount):
        self._name=name
        self.dtype=dtype
        self.maxcount=maxcount
        
        self.channels=set()

    @property
    def name(self):
        return self._name

    def info(self, channel):
        return (self.dtype, self.maxcount)

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

    def post(self,data,dtype,mask=0):
        for c in self.channels:
            c.post(data,dtype,mask)

    def __str__(self):
        return 'PV %(name)s with %(maxcount)d of %(dtype)d'%self.__dict__

class StringPV(PV):
    def __init__(self, name, value=None):
        import time
        PV.__init__(self, name, DBF_STRING , 1)
        self.data=caValue(DBF_STRING)
        if value is not None:
            self.data.value=[value]
            self.data.stamp=time.time()

    def get(self, channel, dtype, count):
        dbf, meta = dbr_to_dbf(dtype)
        if dbf!=DBF_STRING:
            raise CAError("Unsupported type conversion")
        return self.data.tostring(dtype, count)

    def set(self, channel, data, dtype, count):
        dbf, meta = dbr_to_dbf(dtype)
        if dbf!=DBF_STRING:
            raise CAError("Unsupported type conversion")
        print self.data.value
        self.data.fromstring(data, dtype, count)
        print self.data.value
        print 'set',self.name,'to',repr(data)
        return True

