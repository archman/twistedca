# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('TwCA.cac.monitor')
from copy import copy

from twisted.internet import reactor
from twisted.internet.defer import Deferred

from TwCA.util.idman import CBManager
from TwCA.util.cadata import caMeta, fromstring, dbr_to_dbf
from TwCA.util.ca import CAmessage, monitormask
from TwCA.util.defs import *
from TwCA.util.error import ECA_NORMAL, ECA_DISCONN


class CAMonitor(object):
    """A recurring data request
    """
    
    def __init__(self, channel, dbf=None, count=None,
                 meta=META.PLAIN, dbf_conv=None,
                 mask=DBE.VALUE):
        """Start a new request.
        
        channel: PV name
        dbf: Field type requested from server
        count: length requested from server
        meta: Meta-data class requested
        dbf_conv: Additional client side conversion
                  before data is returned to user.
        mask: DBE event mask which will trigger updates

        Note: Server will never return more then count
              elements, but may return less.
        """
        self._chan, self.dbf = channel, dbf
        self._meta, self.count = meta, count
        self.mask,  self.dbf_conv = mask, dbf_conv

        self.subid=None

        if dbf_conv is None and dbf is not None:
            self.meta=caMeta(dbf)
        elif dbf_conv is not None:
            self.meta=caMeta(dbf_conv)
        else:
            self.meta=None

        self._updates=CBManager()

        d=self.__D=self._chan.whenCon
        d.addCallback(self._chanOk)

    @property
    def updates(self):
        """A callback manager for data updates
        
        An instance of CBManager.
        
        Callback called with ((values,meta), mask, status)
        """
        return self._updates

    def close(self):
        """Cancel request
        """
        if self.subid is None:
            return

        if self._chan.sid is not None:
            log.debug('Cancel %s (%d)',self._chan.name,self.mask)
            msg=CAmessage(cmd=2, p1=self._chan.sid,
                                p2=self.subid).pack()
            self._chan._circ.send(msg)

        if self.__D is not None and hasattr(self.__D, 'cancel'):
            self.__D.cancel()
            self.__D=None

        # any updates in the queue will be lost
        if self._chan._circ is not None:
            self._chan._circ.subscriptions.remove(self)
        self.subid=None

        if self._chan.running:
            self._chan._ctxt.closeList.remove(self.close)

        self._updates(None, 0, ECA_DISCONN)

    def _chanOk(self, chan):
        self.__D=None
        if chan is None:
            # channel shutdown
            return
        assert self._chan is chan
        
        ver=chan._circ.version

        self.subid=chan._circ.subscriptions.add(self)

        dbf=self.dbf
        if dbf is None:
            dbf,_=dbr_to_dbf(chan.dbr)
        dbr=dbf_to_dbr(dbf, self._meta)

        # use dynamic array length whenever possible
        cnt=self.count if ver<13 else 0
        if cnt is None or cnt>chan.maxcount:
            cnt=chan.maxcount

        b=monitormask.pack(self.mask)

        msg=CAmessage(cmd=1, size=len(b),
                      dtype=dbr, count=cnt,
                      p1=chan.sid, p2=self.subid,
                      body=b).pack()
        chan._circ.send(msg)
        log.debug('Start monitor %s (%d)',chan.name,self.mask)

        d=self.__D=self._chan.whenDis
        d.addCallback(self._circuitLost)

        return chan

    def _circuitLost(self,_):
        self.__D=None
        if self.subid is None:
            return
        self.subid=None

        self._updates(None, 0, ECA_DISCONN)

        d=self._chan.whenCon
        d.addCallback(self._chanOk)

    def dispatch(self, pkt, circuit, peer=None):
        if pkt.cmd != 1:
            log.warning('Channel %s monitor ignoring pkt %s',self._chan.name,pkt)
            # wait for real reply
            chan._circ.pendingActions[self.subid]=self
            return

        meta=self.meta
        if meta is None:
            dbf,_=dbr_to_dbf(pkt.dtype)
            meta=caMeta(dbf)

        data = fromstring(pkt.body, pkt.dtype, pkt.count, meta)

        self._updates(data, self.mask, pkt.p1)

    def __str__(self):
        cnt='Native' if self.count is None else self.count
        return 'Get %s of %s from %s'%(cnt, self.dbr, self._chan)
