# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('cac.clichannel')

from twisted.internet import reactor
from twisted.internet.defer import Deferred, succeed, fail

from client import CAClient

class CAClientChannel(object):
    S_init='Disconnected'
    S_lookup='PV lookup'
    S_waitcirc='Waiting for circuit'
    S_connect='Connected'
    
    def __init__(self, name, connectCB=None,
                 context=CAClient.default):
        self.name=name
        self._conCB, self._ctxt=connectCB, context
        self._eventDis=Deferred()
        self._eventCon=None
        self._d=None

        self._chan={18:self._channelOk,
                    22:self._rights,
                    26:self._channelFail,
                    27:self._disconn,
                   }

        self._reset()

    def close(self):
        if self._d:
            self._d.errback()

        self._eventDis.callback(self)
        self._eventCon=Deferred()

        self.cid=self.sid=self.dbr=None
        self._circ=self._d=None
        self.maxcount=self.rights=0
        self.state=self.S_init
        

    def _reset(self, delay=0.0):
        self.close()
        
        if self.connected:
            self._conCB(self, False)

        reactor.callLater(delay, self._connect)

    @property
    def connected(self):
        return self.state is self.S_connect

    def _connect(self):
        # the following actions happen in the order:
        # lookup -> getCircuit -> attach -> chanOpen

        def retry(err, delay=0.1):
            self.reset(delay)
            return err

        def chanOpen(conn):
            if conn is False:
                # channel rejected by server
                reactor.callLater(30.0, self._connect)
                return

            self.state=self.S_connect

            self._eventDis=Deferred()
            self._eventCon.callback(self)

            self._conCB(self, True)
            return conn

        def attach(circ):
            log.debug('Attaching %s to %s',self.name,circ)
            circ.addchan(self)
            self._circ=circ

            self._d=Deferred()
            self._d.addCallbacks(chanOpen, retry)
            return circ

        def getCircuit(srv):

            self.state=self.S_waitcirc

            log.debug('Found %s on %s',self.name,srv)
                
            d=self._ctxt.openCircuit(srv)
            d.addCallbacks(attach, retry)
            return srv

        self.state=self.S_lookup

        d=self._ctxt.lookup(self.name)
        d.addCallback(getCircuit)
        # lookups only fail when the client is shutting down

    def _circuitLost(self):
        if self._d:
            self._d.errback()
        
        self._reset()

        if not self._ctxt.running:
            return

        reactor.callLater(0.1, self._connect)

    def _disconn(self, pkt, peer, circuit):
        log.warning('Server has disconnected %s',self.name)

    def _channelOk(self, pkt, peer, circuit):
        self.dbr, self.maxcount=pkt.dtype, pkt.count
        self.sid=pkt.p2

        self._checkReady()

    def _channelFail(self, pkt, peer, circuit):
        log.info('Server %s rejects channel %s',peer,self.name)
        
        self._reset()
        if self._d:
            self._d.callback(False)
            self._d=None

    def _rights(self, pkt, peer, circuit):
        self.rights=pkt.p2
        
        self._checkReady()

    def _checkReady(self):
        if self.sid is None or self.rights is None:
            return
        if self._d:
            self._d.callback(True)
            self._d=None

    def dispatch(self, pkt, peer, circuit):
        assert circuit is self._circ

        if pkt is None:
            log.info('Circuit disconnected %s',self)
            self._conCB(self, False)
            reactor.callLater(0, self._connect)
            return
        
        hdl=self._chan.get(pkt.cmd, self._ctxt.dispatchtcp)
        
        if hdl:
            hdl(pkt, peer, self)
        else:
            log.debug('Channel %s received %s',self.name,pkt)

    def __str__(self):
        return 'Channel %(name)s %(state)s %(cid)s:%(sid)s %(dbr)s %(maxcount)s'%self.__dict__
