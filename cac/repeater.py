# -*- coding: utf-8 -*-

import socket, logging, sys
from socket import INADDR_LOOPBACK, inet_aton
from copy import copy
from struct import Struct

ipv4=Struct('!I')

log=logging.getLogger('cac.repeater')

from util.ca import CAmessage
from util.defs import CLIENT_PORT

from twisted.internet import reactor
from twisted.internet.udp import Port
from twisted.internet.protocol import DatagramProtocol, ConnectedDatagramProtocol
from twisted.internet.error import CannotListenError

class RepeaterNode(ConnectedDatagramProtocol):
    
    def __init__(self, rep, peer):
        self.repeater, self.peer=rep, peer

    def datagramReceived(self, msg, addr):
        
        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)

            if pkt.cmd==23:
                self.transport.write(pkt.pack())
            else:
                log.warning('Unexpected message %d on fanout node',pkt.cmd)

    def connectionFailed(self, _):
        log.debug('Client %s send failed',self.peer)
        self.repeater.regrem(self)
        self.transport.stopListening()

class CARepeaterProtocol(DatagramProtocol):
    
    def __init__(self):
        self.clients=set()

    def regreq(self, peer):
        node=RepeaterNode(self, peer)
        p=Port(0, node, 'localhost')
        p.startListening()
        p.connect(peer[0], peer[1])

        self.clients.add(node)
        log.debug('Repeater add %s',peer)

        rep=CAmessage(cmd=17, p2=INADDR_LOOPBACK)

        node.transport.write(rep.pack())

    def regrem(self, node):
        if node in self.clients:
            self.clients.remove(node)
        else:
            log.error('Who is %s',node)
        log.debug('Repeater del %s',node)

    def repeat(self, pkt):
        log.debug('Fanout %s',pkt)
        for c in self.clients:
            log.debug('to %s',c.peer)
            c.transport.write(pkt.pack())

    def datagramReceived(self, msg, peer):
            
        if len(msg)==0:
            self.regreq(peer)
        
        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)

            if pkt.cmd==24:
                self.regreq(peer)
            elif pkt.cmd==13 and pkt.p2==0:
                pkt.p2=ipv4.unpack(inet_aton(peer[0]))[0]
                self.repeat(pkt)
            else:
                self.repeat(pkt)

def main():
    try:
        p=reactor.listenUDP(CLIENT_PORT, CARepeaterProtocol())
    except CannotListenError:
        sys.exit(1)
    reactor.run()

    p.stopListening()

if __name__=='__main__':
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    main()
