# -*- coding: utf-8 -*-

import logging

log=logging.getLogger('TwCA.cas.pv')

from TwCA.util.defs import *
from TwCA.util.cadata import caMetaProxy, tostring, fromstring
from TwCA.util.error import CAError, ECA_NOCONVERT

class PV(object):
    """Representation of a Process Variable
    
    Holds a value array, meta info, and a maximum size.
    
    A PV instance will receive dbr data directly and
    must perform conversions itself
    """
    
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
        """Return full name of PV"""
        return self._name

    @property
    def maxcount(self):
        """The maximum data array size which is reported to clients.
        
        This should not change over the lifetime of a PV.
        """
        return self._maxcount

    @property
    def count(self):
        """Current data array size."""
        return len(self.value)

    def info(self, channel):
        return (self.meta.dbf, self._maxcount)

    def rights(self, channel):
        """Return rights mask for client on the given channel
        """
        return 3

    def connect(self, channel):
        """Attach new channel to this PV
        """
        self.channels.add(channel)

    def disconnect(self, channel):
        """Called when a channel is closed
        """
        self.channels.remove(channel)

    def get(self, channel, dbr, count):
        """Request for current value of PV.
        Called for gets and when monitors are posted.
        
        Note: No distinction is made between get and post
        """
        try:
            return tostring(self.value, self.meta, dbr, count)
        except ValueError:
            # when no conversion is possible rsrv returns 0
            return tostring([0]*count, self.meta, dbr, count)

    def set(self, channel, data, dbr, count):
        """A Client is sending data
        """

        try:
            val, rmeta = fromstring(data, dbr, count, self.meta)
        except ValueError:
            log.exception("type conversion failed")
            raise CAError("type conversion failed", ECA_NOCONVERT)
        log.info('set %s to %s',self.name,str(val))
        self.value=val
        self.post(DBE.VALUE|DBE.LOG)
        return True

    def post(self,mask):
        """Call to inform monitoring clients of a change
        in the value array
        """
        for c in self.channels:
            c.post(mask)

    def __str__(self):
        vals={'dbf':self.meta.dbf}
        vals.update(self.__dict__)
        return 'PV %(_name)s with %(_maxcount)d of %(dbf)d'%vals
