# -*- coding: utf-8 -*-

import socket, logging
from copy import copy

from zope.interface import implements

from twisted.internet.protocol import Protocol, DatagramProtocol, \
                                      ServerFactory

from TwCA.util import defs
from TwCA.util.ca import CAmessage
from TwCA.util.config import Config
from TwCA.util.idman import DeferredManager

from TwCA.util.interfaces import IConnectNotify

from channel import Channel

log=logging.getLogger('TwCA.cas.endpoint')

class CAcircuit(Protocol):
    implements(IConnectNotify)
    
    def __init__(self, server):
        self.server=server
        self.peer=self.tcpport=None
    
        self.prio, self.version=0, 11

        self.user,self.host="<NOONE>","<ANONYMOUS>"
        
        self.in_buffer=''
        
        self._circ={0 :self.caver,
                    1 :self.forwardchan,
                    2 :self.forwardchan,
                    4 :self.forwardchan,
                    12:self.clearchan,
                    15:self.forwardchan,
                    18:self.createchan,
                    19:self.forwardchan,
                    20:self.caclient,
                    21:self.cahost,
                    23:self.ping,
                   }

        self.__C=DeferredManager()
        self.__D=DeferredManager()
        self.__D.callback(self)
        
        self.channels={}

        self.next_sid=0

    @property
    def whenCon(self):
        return self.__C.get()

    @property
    def whenDis(self):
        return self.__D.get()
    
    def dropchan(self, channel):
        assert channel.sid in self.channels
        self.channels.pop(channel.sid)

    # CA actions

    def caver(self, pkt, x, y):
        self.version=min(defs.CA_VERSION, pkt.count)
        self.prio=pkt.dtype
        log.debug('Version %s',self)

    def caclient(self, pkt, x, y):
        self.user=str(pkt.body).strip('\0')
        log.debug('Update %s',self)

    def cahost(self, pkt, x, y):
        self.host=str(pkt.body).strip('\0')
        # do reverse lookup
        host, aliases, z = socket.gethostbyaddr(self.peer.host)
        if self.host!=host and self.host not in aliases:
            log.warning("""Demoting connection from %s
            reverse lookup against %s failed""",self.peer.host,self.host)
            self.host='<ANONYMOUS>'
            return
        log.debug('Update %s',self)

    def createchan(self, pkt, x, y):
        # Older clients first report version here
        self.version=pkt.p2

        name=str(pkt.body).strip('\0')
        pv = self.server.GetPV(name)

        if pv is None:
            # PV does not exist
            log.debug("Can't create channel for non-existant PV %s",name)
            fail = CAmessage(cmd=26, p1=pkt.p1)
            self.send(fail.pack())
            return

        chan=Channel(self.next_sid, pkt.p1, self.server, self, pv)
        self.channels[chan.sid]=chan
        dtype, maxcount = pv.info(chan)

        ok = CAmessage(cmd=18, dtype=dtype, count=maxcount,
                       p1=pkt.p1, p2=chan.sid)

        rights = CAmessage(cmd=22, p1=pkt.p1, p2=chan.rights)

        self.send(ok.pack()+rights.pack())
        
        self.next_sid=self.next_sid+1
        while self.next_sid in self.channels:
            self.next_sid=self.next_sid+1

    def clearchan(self, pkt, x, y):
        chan=self.channels.get(pkt.p1)
        if not chan:
            log.warning('Attempt to clean non-existent channel')
            return
        
        chan.close()
        ok = CAmessage(cmd=12, p1=pkt.p1, p2=pkt.p2)
        self.send(ok.pack())

    def forwardchan(self, pkt, peer, circuit):
        chan=self.channels.get(pkt.p1)
        if not chan:
            log.warning('Attempt to access non-existent channel')
            return
        chan.dispatch(pkt, peer, circuit)

    def ping(self, pkt, x, y):
        self.send(pkt.pack())

    # socket operations

    def connectionMade(self):
        self.peer=self.transport.getPeer()
        self.tcpport=self.transport.getHost().port

        # before 3.14.12 servers didn't send version until client authenticated
        # from 3.14.12 clients attempting to do TCP name resolution don't authenticate
        # but expect a version message immediately
        pkt=CAmessage(cmd=0, dtype=self.prio, count=defs.CA_VERSION)
        self.send(pkt.pack())
        log.debug('connection from %s',self.peer)
        log.debug('Create %s',self)

        self.server.circuits.add(self)

        self.__D=DeferredManager()
        self.__C.callback(self)

    def connectionLost(self, reason):

        self.__C=DeferredManager()
        D, self.__D = self.__D, None
        D.callback(self)

        self.server.circuits.remove(self)

        log.debug('Destroy %s',self)

    def connectionFailed(self, reason):

        C, self.__C = self.__C, DeferredManager()
        C.callback(None)

    def send(self, msg):
        self.transport.write(msg)

    def sendto(self, msg, peer=None):
        self.transport.write(msg)
    
    def dataReceived(self, msg):

        msg=self.in_buffer+msg

        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)
            
            hdl = self._circ.get(pkt.cmd, self.server.dispatch)
        
            hdl(pkt, self, self.peer)

        self.in_buffer=msg # save remaining

    def __str__(self):
        return 'Circuit v4%(version)d to %(peer)s as %(host)s:%(user)s'% \
            self.__dict__

class CAServerCircuitFactory(ServerFactory):
    
    protocol = CAcircuit
    server = None
    circuits = None
    
    def __init__(self, server):
        self.circuits=set()
        self.server=server
    
    def buildProtocol(self, _):
        return self.protocol(self.server)

class UDPpeer(DatagramProtocol):
    
    def __init__(self, handler, tcpport=Config.default.sport):
        self.handler, self.tcpport=handler, tcpport

    def sendto(self, msg, peer):
        return self.transport.write(msg, peer)

    def datagramReceived(self, msg, peer):
        
        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)
        
            self.handler(pkt, self, peer)

        if len(msg)>0:
            log.warning('dropping incomplete message %s',repr(msg))
