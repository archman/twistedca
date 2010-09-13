# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('cas.server')

from endpoint import UDPpeer, TCPserver
from util.ca import CAmessage, packSearchBody
from socket import htons, htonl, ntohs, ntohl
from defs import *

class Server(object):
    
    def __init__(self, interfaces=('localhost',), pvs=[]):
        self.udp=[]
        self.tcp=[]
        for i in interfaces:
            self.udp.append(UDPpeer(self.dispatchudp,(i,SERVER_PORT)))
            self.tcp.append(TCPserver(self,(i,SERVER_PORT)))

        self._udp={0:self.ignore,6:self.nameres}
        self._tcp={}

        self.pvs={}
        for pv in pvs:
            self.pvs[pv.name]=pv
        
        self.closeList=set()

    def close(self):
        # make a copy of the list (not contents)
        # because calling c() may cause the size
        # of closeList to change
        for c in copy(self.closeList):
            c()
        for ep in self.udp:
            ep.close()
        for ep in self.tcp:
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
        log.info('%s is looking for %s',str(peer),name)
        ret = self.Lookup(name)
        if ret and not isinstance(ret, tuple):
            ret = (0xffffffff, SERVER_PORT)
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
