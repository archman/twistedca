# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('cas.server')

from twisted.internet import reactor,tcp,protocol
from twisted.internet.task import LoopingCall

from endpoint import UDPpeer, CAcircuit
from util.ca import CAmessage, packSearchBody
from util.udp import SharedUDP
from socket import inet_aton
from defs import *

from struct import Struct

ipv4=Struct('!I')

class Server(object):
    
    def __init__(self, interfaces=[('localhost',SERVER_PORT)],
                 pvs=[], reactor=reactor):
        self.reactor=reactor
        self.interfaces=[]

        self.tcpfactory=protocol.ServerFactory()
        self.tcpfactory.protocol=CAcircuit
        self.tcpfactory.server=self

        for addr, tcpport in interfaces:
            tp=reactor.listenTCP(tcpport,
                                 self.tcpfactory,
                                 interface=addr)

            up=SharedUDP(SERVER_PORT,
                         UDPpeer(self.dispatchudp,tcpport),
                         interface=addr,
                         reactor=reactor)
            up.startListening()

            self.interfaces.append((up,tp))

        self._udp={0:self.ignore,6:self.nameres}
        self._tcp={}

        self.pvs={}
        for pv in pvs:
            self.pvs[pv.name]=pv
        
        self.closeList=set()

        self.beaconID=0
        self.beaconTask=LoopingCall(self.sendBeacon)
        self.beaconTask.start(15.0)

    def close(self):
        # make a copy of the list (not contents)
        # because calling c() may cause the size
        # of closeList to change
        for c in copy(self.closeList):
            c()
        for up, tp in self.interfaces:
            up.loseConnection()
            tp.loseConnection()

    def sendBeacon(self):
        b = CAmessage(cmd=13, p1=self.beaconID)

        for up, tp in self.interfaces:
            host = tp.getHost()

            b.p2=ipv4.unpack(inet_aton(host.host))[0]
            b.dtype=host.port

            #TODO: introspect interfaces
            up.write(b.pack(), ('255.255.255.255', CLIENT_PORT))

        self.beaconID=self.beaconID+1

    def dispatchudp(self, pkt, peer, endpoint):
        fn=self._udp.get(pkt.cmd, self.unknown)
        
        fn(pkt, peer, endpoint)

    def dispatchtcp(self, pkt, peer, circuit):
        if pkt is None:
            return # circuit closed
        fn=self._tcp.get(pkt.cmd, self.unknown)
        
        fn(pkt, peer, circuit)

    def ignore(*_):
        pass

    def unknown(self, pkt, peer, endpoint):
        print '>> Unknown <<',peer,'sent',pkt

    def nameres(self, pkt, peer, endpoint):
        name=pkt.body.strip('\0')
        log.info('%s is looking for %s',str(peer),name)
        ret = self.Lookup(name)
        if ret and not isinstance(ret, tuple):
            ret = (0xffffffff, endpoint.tcpport)
        if ret:
            ack=CAmessage(cmd=6, size=8, dtype=ret[1],
                          p1=ret[0], p2=pkt.p2,
                          body=packSearchBody(CA_VERSION))

            endpoint.sendto(ack.pack(), peer)
            
        
    def Lookup(self,name):
        ret=name in self.pvs
        if ret:
            log.info('I have %s',name)
        return ret

    def GetPV(self,name):
        return self.pvs.get(name)
