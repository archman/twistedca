# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('cac.set')

from twisted.internet import reactor
from twisted.internet.defer import Deferred

from TwCA.util.cadata import caMeta, tostring, dbr_to_dbf
from TwCA.util.ca import CAmessage
from TwCA.util.defs import *
from TwCA.util.error import ECA_NORMAL

from client import CAClientShutdown


class CASet(object):
    
    def __init__(self, channel, data,
                 dbf=None,
                 meta=META.PLAIN, dbf_conv=None,
                 wait=False):
        self._chan, self.dbf      = channel, dbf
        self._data, self.dbf_conv = data,    dbf_conv
        self._meta, self._wait    = meta,    wait

        self.done, self.ioid=True, None

        if dbf_conv is None and dbf is not None:
            self.meta=caMeta(dbf)
        elif dbf_conv is not None:
            self.meta=caMeta(dbf_conv)
        else:
            self.meta=None

        self._chan._ctxt.closeList.add(self.close) #TODO: remove

        self.restart(data)

    @property
    def complete(self):
        return self._comp

    def close(self):
        if not self.done and self._comp:
            self._comp.errback(CAClientShutdown('Set aborted'))

    def restart(self, data):
        if not self.done:
            raise RuntimeError('Previous Set not complete')
        self._data=data

        self.done=False

        self._comp=Deferred()

        d=self._chan._eventCon
        d.addCallback(self._chanOk)

    def _chanOk(self, chan):
        assert self._chan is chan

        self.ioid=chan._circ.pendingActions.add(self)

        dbf=self.dbf
        if dbf is None:
            dbf,_=dbr_to_dbf(chan.dbr)
        dbr=dbf_to_dbr(dbf, self._meta)

        meta=self.meta
        if meta is None:
            meta=caMeta(dbf)

        data=self._data
        cnt=len(data)
        if cnt > chan.maxcount:
            cnt=chan.maxcount
            data=data[:chan.maxcount]

        data, cnt = tostring(data, meta, dbr, cnt)

        log.debug('Set %s to %s',chan,data)

        cmd = 19 if self._wait else 4

        msg=CAmessage(cmd=cmd, size=len(data),
                      dtype=dbr, count=cnt,
                      p1=chan.sid, p2=self.ioid,
                      body=data).pack()
        chan._circ.send(msg)

        if not self._wait:
            # do completion here
            self.ioid=None
            self.done=True
            self._comp.callback(ECA_NORMAL)

        return chan

    def _circuitLost(self,_):
        self.ioid=None
        if self.done:
            return

        d=self._chan._eventCon
        d.addCallback(self._chanOk)

    def dispatch(self, pkt, peer, circuit):
        if pkt.cmd != 19:
            log.warning('Channel %s get ignoring pkt %s',self._chan.name,pkt)
            # wait for real reply
            chan._circ.pendingActions[self.ioid]=self
            return

        self.ioid=None
        self.done=True

        # mark done so callback can restart
        if pkt.p1==ECA_NORMAL:
            self._comp.callback(ECA_NORMAL)
        else:
            self._comp.errback(pkt.p1)


    def __str__(self):
        cnt='Native' if self.count is None else self.count
        return 'Set %s of %s from %s'%(cnt, self.dbr, self._chan)

