# -*- coding: utf-8 -*-

import socket, logging
from copy import copy

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet.defer import Deferred, maybeDeferred

from TwCA.util.ca import CAmessage, padString
from TwCA.util import defs
from TwCA.util.idman import IDManager

log=logging.getLogger('cac.circuit')

class CAClientcircuit(Protocol):

    def __init__(self):
        self.client, self.peer=None, None
    
        self.prio, self.version=0, 10
        
        self.in_buffer=''
        
        self._circ={0 :self.caver,
                    1 :self.forwardSubID,
                    15:self.forwardIOID,
                    18:self.forwardCID,
                    19:self.forwardIOID,
                    22:self.forwardCID,
                    23:self.ping,
                    26:self.forwardCID,
                    27:self.forwardCID,
                   }
        
        self.channels=IDManager()
        self.subscriptions=IDManager()
        self.pendingActions=IDManager()


    def addchan(self, channel):
        assert channel not in self.channels
        
        channel.cid=self.channels.add(channel)

        name=padString(channel.name)
        msg=CAmessage(cmd=18, size=len(name),
                      p1=channel.cid, p2=defs.CA_VERSION,
                      body=name).pack()

        self.transport.write(msg)
    
    def dropchan(self, channel):
        assert channel in self.channels

        self.channels.pop(channel.cid)

        msg=CAmessage(cmd=12, p1=channel.sid, p2=channel.cid).pack()
        self.transport.write(msg)
        
        if len(self.channels)!=0:
            return

        self.loseConnection()

    # CA actions

    def caver(self, pkt, x, y):
        self.version=min(defs.CA_VERSION, pkt.count)
        self.prio=pkt.dtype
        log.debug('Version %s',self)

    def ping(self, pkt, x, y):
        self.send(pkt.pack())

    def forwardCID(self, pkt, peer, circuit):
        chan=self.channels.get(pkt.p1)
        if chan is None:
            log.warning('Attempt to access non-existent CID %d',pkt.p1)
            return
        chan.dispatch(pkt, peer, circuit)

    def forwardIOID(self, pkt, peer, circuit):

        act=self.pendingActions.pop(pkt.p2, None)
        if act is None:
            log.warning('Reply for non-existent action %d',pkt.p2)
            return
        act.dispatch(pkt, peer, circuit)

    def forwardSubID(self, pkt, peer, circuit):

        act=self.subscriptions.get(pkt.p2, None)
        if act is None:
            log.warning('Reply for non-existent subscription %d',pkt.p2)
            return
        act.dispatch(pkt, peer, circuit)

    # socket operations

    def connectionMade(self):
        self.client=self.factory.client
        self.peer=self.transport.getPeer()
        log.debug('Open %s',self)
        
        user=padString(self.client.user)
        host=padString(self.client.host)

        msg=CAmessage(cmd=0, dtype=self.prio, count=defs.CA_VERSION).pack()
        msg+=CAmessage(cmd=20, size=len(user), body=user).pack()
        msg+=CAmessage(cmd=21, size=len(host), body=host).pack()
        
        self.transport.write(msg)
        
        self.factory.circuitReady(self.transport.connector, self)

    def connectionLost(self, reason):
        self.client.dispatchtcp(None, self.peer, self)
        # make a copy of the list (not contents)
        # because calling _circuitLost() may cause the size
        # of closeList to change
        for m in [self.channels, self.subscriptions, self.pendingActions]:
            for c in m.itervalues():
                c._circuitLost()
            m.clear()

        log.debug('Destroy %s',self)

    def send(self, msg):
        self.transport.write(msg)
    
    def dataReceived(self, msg):

        msg=self.in_buffer+msg

        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)
            
            hdl = self._circ.get(pkt.cmd, self.client.dispatchtcp)
        
            hdl(pkt, self.peer, self)

        self.in_buffer=msg # save remaining

    def __str__(self):
        return 'Client Circuit v4%(version)d to %(peer)s'% \
            self.__dict__

class CACircuitFactory(ClientFactory):
    
    protocol = CAClientcircuit

    def __init__(self, client):
        self.client=client
        self.circuits={}

    def close(self):
        for c in copy(self.circuits.values()):
            c.disconnect()

    def requestCircuit(self, srv):
        circ=self.circuits.get(srv)
        if circ is None:

            host, port = srv

            circ=reactor.connectTCP(host, port, self, timeout=15)
            circ.circDeferred=Deferred()
            circ.circDest=srv
            self.circuits[srv]=circ

        return circ.circDeferred

    def circuitReady(self, circ, proto):
        assert circ.circDest in self.circuits

        circ.circDeferred.callback(proto)

    def clientConnectionFailed(self, circ, _):
        assert circ.circDest in self.circuits

        circ.circDeferred.errback()

        self.circuits.pop(circ.circDest)

    def clientConnectionLost(self, circ, _):
        assert circ.circDest in self.circuits

        self.circuits.pop(circ.circDest)

