# -*- coding: utf-8 -*-

import socket, logging
from copy import copy

from zope.interface import implements

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet.defer import Deferred, succeed
from twisted.internet.tcp import Connector

from TwCA.util.ca import CAmessage, padString
from TwCA.util import defs
from TwCA.util.idman import IDManager
from TwCA.util.twistedhelper import DeferredConnector

from interfaces import IClientcircuit

log=logging.getLogger('cac.circuit')

class CAClientcircuit(Protocol):
    """Protocol for speaking to a CA server
    """
    
    implements(IClientcircuit)

    def __init__(self, client):
        self.peer=None
        self.client=client
    
        self.prio, self.version=0, 11
        
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
        """Add a channel to this circuit
        """
        assert channel not in self.channels
        
        channel.cid=self.channels.add(channel)

        name=padString(channel.name)
        msg=CAmessage(cmd=18, size=len(name),
                      p1=channel.cid, p2=defs.CA_VERSION,
                      body=name).pack()

        self.transport.write(msg)
    
    def dropchan(self, channel):
        """Remove a channel from this circuit
        """
        assert channel in self.channels

        self.channels.pop(channel.cid)

        msg=CAmessage(cmd=12, p1=channel.sid, p2=channel.cid).pack()
        self.transport.write(msg)
        
        if len(self.channels)!=0:
            return

        self.loseConnection()

    # CA actions

    def caver(self, pkt, _):
        self.version=min(defs.CA_VERSION, pkt.count)
        self.prio=pkt.dtype
        log.debug('Version %s',self)

    def ping(self, pkt, _):
        self.send(pkt.pack())

    def forwardCID(self, pkt, circuit):
        chan=self.channels.get(pkt.p1)
        if chan is None:
            log.warning('Attempt to access non-existent CID %d',pkt.p1)
            return
        chan.dispatch(pkt, circuit)

    def forwardIOID(self, pkt, circuit):

        act=self.pendingActions.pop(pkt.p2, None)
        if act is None:
            log.warning('Reply for non-existent action %d',pkt.p2)
            return
        act.dispatch(pkt, peer, circuit)

    def forwardSubID(self, pkt, circuit):

        act=self.subscriptions.get(pkt.p2, None)
        if act is None:
            log.warning('Reply for non-existent subscription %d',pkt.p2)
            return
        act.dispatch(pkt, circuit)

    # socket operations

    def connectionMade(self):
        self.peer=self.transport.getPeer()
        log.debug('Open %s',self)
        
        user=padString(self.client.user)
        host=padString(self.client.host)

        msg=CAmessage(cmd=0, dtype=self.prio, count=defs.CA_VERSION).pack()
        msg+=CAmessage(cmd=20, size=len(user), body=user).pack()
        msg+=CAmessage(cmd=21, size=len(host), body=host).pack()
        
        self.transport.write(msg)
        
        if hasattr(self.transport.connector, 'connectionMade'):
            # the testing transports have no connector
            self.transport.connector.connectionMade()

    def connectionLost(self, reason):
        log.debug('Destroy %s',self)

    def send(self, msg):
        self.transport.write(msg)
    
    def dataReceived(self, msg):

        msg=self.in_buffer+msg

        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)
            
            hdl = self._circ.get(pkt.cmd, self.client.dispatch)
        
            hdl(pkt, self)

        self.in_buffer=msg # save remaining

    def __str__(self):
        return 'Client Circuit v4%(version)d to %(peer)s'% \
            self.__dict__

class CACircuitFactory(ClientFactory):
    """Handles circuit life cycle
    
    Maintains a list of open circuits to avoid duplication.
    """
    
    protocol = CAClientcircuit
    
    timeout = 10
    
    class CACircuitConnector(DeferredConnector):
        """Need to ensure that the factory has
        dropped the circuit before we inform clients
        so that a new request can be safely made from
        the Deferred callback
        """
        
        def connectionLost(self, res):
            self.factory.ConnectorLost(self, res)
            DeferredConnector.connectionLost(self, res)

        def connectionFailed(self, res):
            self.factory.ConnectorFailed(self, res)
            DeferredConnector.connectionFailed(self, res)

    def __init__(self, client):
        self.client=client
        self.circuits={}

    def close(self):
        for c in copy(self.circuits.values()):
            c._persist=False
            c.disconnect()
        self.client=None

    def buildProtocol(self,_):
        return CAClientcircuit(self.client)

    def requestCircuit(self, srv, persist=None):
        """Request a new circuit to a CA server.
        
        srv: tuple (host ip, port)
        persist: Make circuit persistent (auto re-connect)
        
        Returns a tuple which is called with either an
        instance of CAClientcircuit or None if the server
        could not be contacted.
        """
        if self.client is None:
            return succeed(None)

        circ=self.circuits.get(srv)
        if circ is None:

            host, port = srv

            circ=self.CACircuitConnector(host, port, self,
                                   timeout=self.timeout,
                                   bindAddress=None,
                                   reactor=self.client.reactor)
            circ.connect()
            circ.circDest=srv
            circ._persist=False
            self.circuits[srv]=circ

        if persist is not None:
            circ._persist=persist

        return circ.whenCon

    def ConnectorFailed(self, circ, _):
        assert circ.circDest in self.circuits
        if not circ._persist:
            self.circuits.pop(circ.circDest)

    def clientConnectionFailed(self, circ, _):
        if circ._persist:
            reactor.callLater(self.timeout/2.0, circ.connect)

    def ConnectorLost(self, circ, _):
        assert circ.circDest in self.circuits

        if not circ._persist:
            self.circuits.pop(circ.circDest)
            return

    def clientConnectionLost(self, circ, _):
        if not circ._persist:
            return
        log.debug('Reconnect persistent circuit to %s',
                  circ.circDest)
        circ.connect()

