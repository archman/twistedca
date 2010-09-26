# -*- coding: utf-8 -*-

import socket, logging
from util.ca import CAmessage
from channel import Channel
from util import defs
from copy import copy

from twisted.internet.protocol import Protocol, DatagramProtocol

log=logging.getLogger('cas.endpoint')

class CAcircuit(Protocol):
    
    def __init__(self):
        self.server, self.peer=None, None
    
        self.prio, self.version=0, 10

        self.user,self.host=None,None
        
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

        self.closeList=set()
        
        self.channels={}

        self.next_sid=0
    
    def dropchan(self, channel):
        self.channels.pop(channel.sid)

    # CA actions

    def caver(self, pkt, x, y):
        self.version=pkt.count
        self.prio=pkt.dtype
        log.debug('Version %s',self)

    def caclient(self, pkt, x, y):
        self.user=pkt.body.strip('\0')
        log.debug('Update %s',self)
        self.circuitReady()

    def cahost(self, pkt, x, y):
        self.host=pkt.body.strip('\0')
        # do reverse lookup
        host, aliases, z = socket.gethostbyaddr(self.peer.host)
        if self.host!=host and self.host not in aliases:
            log.warning("""Demoting connection from %s
            reverse lookup against %s failed""",self.peer.host,self.host)
            self.host='<ANONYMOUS>'
            return
        log.debug('Update %s',self)
        self.circuitReady()

    def circuitReady(self):
        if self.user is None or self.host is None:
            return
        log.debug('Circuit ready')
        pkt=CAmessage(cmd=0, dtype=self.prio, count=defs.CA_VERSION)
        self.send(pkt.pack())

    def createchan(self, pkt, x, y):
        # Older clients first report version here
        self.version=pkt.p2

        name=pkt.body.strip('\0')
        pv = self.server.GetPV(name)

        if pv is None:
            # PV does not exist
            fail = CAmessage(cmd=26, p1=pkt.p1)
            self.send(fail.pack())
            return

        chan=Channel(self.next_sid, pkt.p1, self.server, self, pv)
        self.channels[chan.sid]=chan
        dtype, maxcount = pv.info(chan)

        ok = CAmessage(cmd=18, dtype=dtype, count=maxcount,
                       p1=pkt.p1, p2=chan.sid)

        rights = CAmessage(cmd=22, p1=pkt.p1, p2=pv.rights(chan))

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
        self.server=self.factory.server
        self.peer=self.transport.getPeer()
        log.debug('connection from %s',self.peer)
        log.debug('Create %s',self)

    def connectionLost(self, reason):
        self.server.dispatchtcp(None, self.peer, self)
        # make a copy of the list (not contents)
        # because calling c() may cause the size
        # of closeList to change
        for c in copy(self.closeList):
            c()

        log.debug('Destroy %s',self)

    def send(self, msg):
        self.transport.write(msg)
    
    def dataReceived(self, msg):

        msg=self.in_buffer+msg

        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)
            
            hdl = self._circ.get(pkt.cmd, self.server.dispatchtcp)
        
            hdl(pkt, self.peer, self)

        self.in_buffer=msg # save remaining

    def __str__(self):
        return 'Circuit v4%(version)d to %(peer)s as %(host)s:%(user)s'% \
            self.__dict__


class UDPpeer(DatagramProtocol):
    
    def __init__(self, handler, tcpport=defs.SERVER_PORT):
        self.handler, self.tcpport=handler, tcpport

    def sendto(self, msg, peer):
        return self.transport.write(msg, peer)

    def datagramReceived(self, msg, peer):
        
        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)
        
            self.handler(pkt, peer, self)

        if len(msg)>0:
            log.warning('dropping incomplete message %s',repr(msg))
