# -*- coding: utf-8 -*-

from endpoint import UDPpeer, TCPserver
from util.ca import CAmessage, packSearchBody
from socket import htons, htonl, ntohs, ntohl
from defs import *

class Server(object):
    
    def __init__(self, interfaces=('localhost',), names=[]):
        self.udp=[]
        self.tcp=[]
        for i in interfaces:
            self.udp.append(UDPpeer(self.dispatchudp,(i,SERVER_PORT)))
            self.tcp.append(TCPserver(self.dispatchtcp,(i,SERVER_PORT)))

        self._udp={0:self.ignore,6:self.nameres}
        self._tcp={}

        self.names=names

    def close(self):
        for ep in self.udp:
            ep.close()

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
        print peer,'sent',pkt

    def nameres(self, pkt, peer, endpoint):
        name=pkt.body.strip('\0')
        print peer,pkt.count,'is looking for',repr(name),''
        ret = self.Lookup(name)
        if ret and not isinstance(ret, tuple):
            ret = (0xffffffff, SERVER_PORT)
        if ret:
            ack=CAmessage(cmd=6, size=8, dtype=ret[1],
                          p1=ret[0], p2=pkt.p2,
                          body=packSearchBody(CA_VERSION))
            print 'reply with',ack
            endpoint.sendto(ack.pack(), peer)
            
        
    def Lookup(self,name):
        return name in self.names
