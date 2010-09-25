# -*- coding: utf-8 -*-

import socket, logging
from socket import inet_aton

log=logging.getLogger('cac.endpoint')

from util.ca import CAmessage
from util.defs import CLIENT_PORT

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, DatagramProtocol
from twisted.internet.address import IPv4Address

class RepClient(DatagramProtocol):
    
    def __init__(self, handler):
        self.handler=handler

    def doStart(self):
        host=self.transport.getHost()
        addr, self.port = host.host, host.port
        
        self.rep=IPv4Address('UDP',addr,CLIENT_PORT)

        reg=CAmessage(cmd=24, p2=inet_aton(addr))
        self.sendto(reg.pack())
        
        self.waitack=reactor.callLater(2.0, self.noack)

    def ackreg(self, pkt):
        self.waitack.cancel()

    def noack(self):
        log.error("Failed to connect to CA Repeater")

    def sendto(self, msg):
        return self.transport.write(msg, self.rep)

    def datagramReceived(self, msg, peer):
        if peer != self.rep:
            log.warning('dropping UDP traffic from %s',peer)
            return
        
        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)
        
            if pkt.cmd!=17:
                self.handler(pkt, self)
            else:
                self.ackreg(pkt)

        if len(msg)>0:
            log.warning('dropping incomplete message')

