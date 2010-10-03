# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('cac.get')

from twisted.internet import reactor
from twisted.internet.defer import Deferred

from util.cadata import caMeta, fromstring, dbr_to_dbf
from util.ca import CAmessage


class CAGet(object):
    
    def __init__(self, channel, dbr, count=None, dbf=None):
        self._chan, self.dbr, self.count = channel, dbr, count
        self.ioid=None

        if dbf is None:
            dbf, _=dbr_to_dbf(self.dbr)

        self.meta=caMeta(dbf)

        self.restart()

    def restart(self):
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

        cnt=self.count
        if cnt is None:
            cnt=chan.maxcount

        msg=CAmessage(cmd=15, dtype=self.dbr, count=cnt,
                      p1=chan.sid, p2=self.ioid).pack()
        chan._circ.send(msg)

        return chan

    def _circuitLost(self):
        self.ioid=None
        if self.done:
            return

        d=channel._eventCon
        d.addCallback(self._chanOk)

    def dispatch(self, pkt, peer, circuit):
        if pkt.cmd != 15:
            log.warning('Channel %s get ignoring pkt %s',self._chan.name,pkt)
            # wait for real reply
            chan._circ.pendingActions[self.ioid]=self
            return

        data = fromstring(pkt.body, pkt.dtype, pkt.count, self.meta)

        self._result.callback(data)
        self.ioid=None
        self.done=True

    def __str__(self):
        cnt='Native' if self.count is None else self.count
        return 'Get %s of %s from %s'%(cnt, self.dbr, self._chan)
