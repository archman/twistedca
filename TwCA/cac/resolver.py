# -*- coding: utf-8 -*-

import logging, socket
log=logging.getLogger('cac.resolver')
from errno import EPERM
from copy import copy

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, DatagramProtocol
from twisted.internet.defer import Deferred
from twisted.internet.udp import Port
from twisted.python.failure import Failure

from TwCA.util.defs import SERVER_PORT, CA_VERSION
from TwCA.util.config import Config
from TwCA.util.ca import CAmessage, searchbody, padString
from TwCA.util.ifinspect import getifinfo
from TwCA.cas.endpoint import UDPpeer
    
class Cancelled(Exception):
    pass

class Request(object):
    
    def __init__(self, name, id, manager):
        self.name, self.id, self.manager=name, id, manager

        self.d=Deferred()
        
        self.wait=0.04
        self.T=None
        self.Skip=set()
        
        nbody=padString(name)
        self.msg=CAmessage(cmd=0, count=CA_VERSION).pack()
        self.msg+=CAmessage(cmd=6, size=len(nbody), dtype=5,
                           count=CA_VERSION,
                           p1=id, p2=id, body=nbody
                          ).pack()

        self.lookup()

    def lookup(self):
        self.manager._query(self)
        self.T=reactor.callLater(self.wait, self.lookup)
        self.wait=min(self.wait*2, 30.0)

    def received(self, srv):
        if self.T is not None:
            self.T.cancel()
            self.T=None
        self.d.callback(srv)

    def cancel(self):
        if self.T is not None:
            self.T.cancel()
            self.T=None

        # once the manager is informed future requests
        # for this name will result in a new request
        self.manager._cancel(self)

        # The cancel will propogate through all handlers
        # so we must catch it at the end to avoid
        # an 'Unhandled error in Deferred:' warning
        self.d.addErrback(lambda x:x.trap(Cancelled))

        self.d.errback(Cancelled('Request cancelled'))

class Resolver(object):
    
    def __init__(self, tcpfactory=None, conf=Config.default):
        self.tcpfactory=tcpfactory

        self._udp=Port(0, UDPpeer(self._dataRx, 0))
        self._udp.startListening()
        self._udp.getHandle().setsockopt(socket.SOL_SOCKET,
                                    socket.SO_BROADCAST, 1)

        self.nextID=0
        # requests indexed by id and name
        self.reqID={}
        self.reqName={}

        self.tcpReady=set()

        if tcpfactory is not None:
            for srv in conf.nameservs:
                d=tcpfactory.requestCircuit(srv, persist=True)
                d.addCallback(self.nameservReady)

        self.addrs=set()
        if conf.autoaddrs:
            for intr in getifinfo():
                addr=(intr.broadcast, conf.sport)
                if intr.broadcast is None:
                    continue
                self.addrs.add(addr)

        for addr in conf.addrs:
            self.addrs.add(addr)

    def nameservReady(self, circ):
        log.debug('Resolver TCP ready %s',circ)
        self.tcpReady.add(circ)
        circ.transport.connector.circLost.addCallback(self._circuitLost)
        return circ

    def _circuitLost(self, circ):
        self.tcpReady.remove(circ)
        # can only get here if tcpfactory is not None
        d=self.tcpfactory.requestCircuit(circ.transport.connector.circDest, persist=True)
        d.addCallback(self.nameservReady)
        log.debug('Resolver waiting for %s',circ)
        return circ

    def close(self):
        self._udp.stopListening()

        # req.cancel() will modify reqID
        for req in copy(self.reqID.values()):
            req.cancel()
            
        assert len(self.reqID)==0
        assert len(self.reqName)==0

    def lookup(self, name):
        req=self.reqName.get(name)
        
        if req is None:
            req=Request(name, self.nextID, self)
            self.reqID[req.id]=req
            self.reqName[req.name]=req
            
            while self.nextID in self.reqID:
                self.nextID+=1

        return req.d

    def _cancel(self, req):
        self.reqID.pop(req.id)
        self.reqName.pop(req.name)

    def _query(self, req):

        # UDP endpoints
        for addr in self.addrs:

            try:
                self._udp.write(req.msg, addr)
            except socket.error, e:
                if e.errno!=EPERM:
                    raise

        for sock in self.tcpReady:
            sock.send(req.msg)

    def _dataRx(self, pkt, srv, _):
        if pkt.cmd==0:
            pass

        elif pkt.cmd==6:

            req=self.reqID.pop(pkt.p2, None)
            if req is None:
                log.warning('Ignored reply for non-existent search')
                return
            self.reqName.pop(req.name)

            req.received((srv[0], pkt.dtype))

        elif pkt.cmd==14:
            
            req=self.reqID.get(pkt.p2)
            if req is None:
                log.warning('Ignored reply for non-existent search')
                return

            # exclude from future searches
            req.Skip.add(srv)

        else:
            log.warning('Name receiver ignored unexpected msg %u',pkt.cmd)

def test():
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    
    r=Resolver()
    
    def start(name):
        dx=r.lookup(name)
        dx.addCallback(found, name)

    def found(srv, name):
        if srv is None:
            return
        print 'found',name,'on',srv
        reactor.callLater(5, start, name)
    
    start('test')
    start('test2')

    reactor.run()

if __name__=='__main__':
    test()
