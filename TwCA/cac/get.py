# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('cac.get')

from twisted.internet import reactor
from twisted.internet.defer import Deferred

from TwCA.util.cadata import caMeta, fromstring, dbr_to_dbf
from TwCA.util.ca import CAmessage
from TwCA.util.defs import *

from client import CAClientShutdown


class CAGet(object):
    """A non-recuring request for data
    """
    
    def __init__(self, channel, dbf=None, count=None,
                 meta=META.PLAIN, dbf_conv=None):
        """Start a new request.
        
        channel: PV name
        dbf: Field type requested from server
        count: length requested from server
        meta: Meta-data class requested
        dbf_conv: Additional client side conversion
                  before data is returned to user.

        Note: Server will never return more then count
              elements, but may return less.
        """
        self._chan, self.dbf = channel, dbf
        self._meta, self.count = meta, count
        self.dbf_conv=dbf_conv

        self.done, self.ioid=True, None

        if dbf_conv is None and dbf is not None:
            self.meta=caMeta(dbf)
        elif dbf_conv is not None:
            self.meta=caMeta(dbf_conv)
        else:
            self.meta=None

        self._chan._ctxt.closeList.add(self.close) #TODO: remove

        self.restart()

    def close(self):
        """Cancel request
        """
        if not self.done:
            self._result.errback(CAClientShutdown('Get aborted'))

    def restart(self):
        """Restart request
        
        Send a new request to the server.
        
        Note: A no-op if a request is currently in progress.
        """
        if not self.done:
            return

        self.done=False

        self._result=Deferred()

        d=self._chan._eventCon
        d.addCallback(self._chanOk)

    @property
    def data(self):
        """A Deferred which will be called with the result
        
        Will be called with a tuple (value array, caMeta)
        """
        return self._result

    def _chanOk(self, chan):
        assert self._chan is chan
        
        ver=chan._circ.version

        self.ioid=chan._circ.pendingActions.add(self)

        dbf=self.dbf
        if dbf is None:
            dbf,_=dbr_to_dbf(chan.dbr)
        dbr=dbf_to_dbr(dbf, self._meta)

        # use dynamic array length whenever possible
        cnt=self.count if ver<13 else 0
        if cnt is None or cnt>chan.maxcount:
            cnt=chan.maxcount

        msg=CAmessage(cmd=15, dtype=dbr, count=cnt,
                      p1=chan.sid, p2=self.ioid).pack()
        chan._circ.send(msg)

        return chan

    def _circuitLost(self,_):
        self.ioid=None
        if self.done:
            return

        d=self._chan._eventCon
        d.addCallback(self._chanOk)

    def dispatch(self, pkt, peer, circuit):
        if pkt.cmd != 15:
            log.warning('Channel %s get ignoring pkt %s',self._chan.name,pkt)
            # wait for real reply
            chan._circ.pendingActions[self.ioid]=self
            return

        meta=self.meta
        if meta is None:
            dbf,_=dbr_to_dbf(pkt.dtype)
            meta=caMeta(dbf)

        data = fromstring(pkt.body, pkt.dtype, pkt.count, meta)

        self.ioid=None
        self.done=True
        self._result.callback(data)

    def __str__(self):
        cnt='Native' if self.count is None else self.count
        return 'Get %s of %s from %s'%(cnt, self.dbr, self._chan)
