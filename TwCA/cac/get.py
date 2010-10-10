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
    
    def __init__(self, channel, dbf=None, count=None,
                 meta=META.PLAIN, dbf_conv=None):
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
        if not self.done:
            self._result.errback(CAClientShutdown('Get aborted'))

    def restart(self):
        if not self.done:
            return

        self.done=False

        self._result=Deferred()

        d=self._chan._eventCon
        d.addCallback(self._chanOk)

    @property
    def data(self):
        return self._result

    def _chanOk(self, chan):
        assert self._chan is chan

        self.ioid=chan._circ.pendingActions.add(self)

        dbf=self.dbf
        if dbf is None:
            dbf,_=dbr_to_dbf(chan.dbr)
        dbr=dbf_to_dbr(dbf, self._meta)

        cnt=self.count
        if cnt is None:
            cnt=chan.maxcount

        msg=CAmessage(cmd=15, dtype=dbr, count=cnt,
                      p1=chan.sid, p2=self.ioid).pack()
        chan._circ.send(msg)

        return chan

    def _circuitLost(self):
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

        self._result.callback(data)
        self.ioid=None
        self.done=True

    def __str__(self):
        cnt='Native' if self.count is None else self.count
        return 'Get %s of %s from %s'%(cnt, self.dbr, self._chan)
