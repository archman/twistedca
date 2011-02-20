# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('TwCA.cac.set')

from twisted.internet import reactor
from twisted.internet.defer import CancelledError

from TwCA.util.idman import DeferredManager
from TwCA.util.cadata import caMeta, tostring, dbr_to_dbf
from TwCA.util.ca import CAmessage
from TwCA.util.defs import *
from TwCA.util.error import ECA_NORMAL


class CASet(object):
    """Write to a PV
    """
    
    def __init__(self, channel, data,
                 dbf=None,
                 meta=META.PLAIN, dbf_conv=None,
                 wait=False):
        """Start a new write request
        
        channel: PV name
        data: value array
        dbf: Field type to write
        meta: Meta data class to send
        dbf_conv: Treat value array as different field type.
                  Does a client-side conversion
        wait: Request notification on completion
        """
        self._chan, self.dbf      = channel, dbf
        self._data, self.dbf_conv = data,    dbf_conv
        self._meta, self._wait    = meta,    wait

        self.done, self.ioid=True, None
        self.__D=None

        if dbf_conv is None and dbf is not None:
            self.meta=caMeta(dbf)
        elif dbf_conv is not None:
            self.meta=caMeta(dbf_conv)
        else:
            self.meta=None

        self.restart(data)

    @property
    def complete(self):
        """A Deferred called when the write has finished.
        
        This is either when the request is sent, or when
        confirmation is received depending on the type of
        write.
        """
        return self._comp.get()

    def close(self):
        """Cancel the request
        """
        if self._chan is None:
            return # already shutdown

        if not self.done and self._comp:
            self._comp.callback(None)

        if self.__D is not None and hasattr(self.__D, 'cancel'):
            d,  self.__D = self.__D,  None
            d.addErrback(lambda e:e.trap(CancelledError))
            d.cancel()

        self._chan=None

    def restart(self, data):
        """Re-send with new value array
        """
        if not self.done:
            raise RuntimeError('Previous Set not complete')
        self._data=data

        self.done=False

        self._comp=DeferredManager()

        d=self.__D=self._chan.whenCon
        d.addCallback(self._chanOk)

    def _chanOk(self, chan):
        self.__D=None
        if chan is None:
            self.close()
            # channel has shutdown
            return
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
            log.debug('Send put request (no wait) %s',self._chan.name)
            # do completion here
            self.ioid=None
            self.done=True
            self._comp.callback(ECA_NORMAL)

        else:
            log.debug('Send put request (wait) %s',self._chan.name)
            d=self.__D=self._chan.whenDis
            d.addCallback(self._circuitLost)

        return chan

    def _circuitLost(self,_):
        self.__D=None
        self.ioid=None
        if self.done:
            return

        d=self.__D=self._chan.whenCon
        d.addCallback(self._chanOk)

    def dispatch(self, pkt, circuit, peer=None):
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

