# -*- coding: utf-8 -*-

from defs import *

class CAError(Exception):
    def __init__(self, msg):
        self.msg=msg
    def __str__(self):
        return 'CAError: '+str(self.msg)

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
    def __init__(self, name, value=''):
        PV.__init__(self, name, DBF_STRING , 1)
        self.val=value

    def get(self, channel, dtype, count):
        if dtype!=DBF['string']:
            raise CAError("Unsupported type conversion")
        return self.val

    def set(self, channel, data, dtype, count):
        if dtype!=DBF['string']:
            raise CAError("Unsupported type conversion")
        print 'set',self.name,'to',repr(data)
        return True

