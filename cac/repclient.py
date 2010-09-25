# -*- coding: utf-8 -*-

import socket, logging
from socket import inet_aton

log=logging.getLogger('cac.repclient')

from util.ca import CAmessage
from util.defs import CLIENT_PORT

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.internet.protocol import Protocol, DatagramProtocol
from twisted.internet.address import IPv4Address
from twisted.internet.error import CannotListenError

__all__=['client']

class RepClient(DatagramProtocol):
    
    def __init__(self, port=CLIENT_PORT):
        self.handlers=set()
        self.port=port
        self.waitack=None
        
        self.rep=('127.0.0.1',port)

    def stopProtocol(self):
        if self.waitack:
            self.waitack.cancel()
            self.waitack=None

    def sendReg(self):
        if self.waitack:
            self.waitack.cancel()
            self.waitack=None

        self.sendto('')
        
        self.waitack=reactor.callLater(2.0, self.noack)

    def ackreg(self, pkt):
        if self.waitack:
            self.waitack.cancel()
            self.waitack=None

    def noack(self):
        log.error("Failed to connect to CA Repeater")
        self.sendto('')
        self.waitack=reactor.callLater(4.0, self.noack)

    def sendto(self, msg):
        return self.transport.write(msg, self.rep)

    def datagramReceived(self, msg, peer):
        
        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)
        
            if pkt.cmd!=17:
                for h in self.handlers:
                    h(pkt, peer)
            else:
                self.ackreg(pkt)

        if len(msg)>0:
            log.warning('dropping incomplete message')

class RepManager(object):
    
    def __init__(self, port=CLIENT_PORT):
        self._port=reactor.listenUDP(0, RepClient(), 'localhost')
        
        self._watcher=LoopingCall(self.check)
        self._watcher.start(30.0, now=False)
        
        self.check(first=True)
        
        reactor.addSystemEventTrigger("before", "shutdown", self.close)

    def check(self,first=False):
        try:
            import subprocess, os, sys, time

            R=reactor.listenUDP(self._port.protocol.port, DatagramProtocol())
            R.stopListening()

            log.info('Starting repeater')
            subprocess.Popen([sys.executable, "-m", "cac.repeater"],
                             close_fds=True)
            
            reactor.callLater(0.5, self._port.protocol.sendReg)
        except CannotListenError:
            if first:
                self._port.protocol.sendReg()

    def close(self):
        log.debug('Repeater client stopping')
        self._watcher.stop()
        self._port.stopListening()

    def add(self, handler):
        self._port.protocol.handlers.add(handler)

    def remove(self, handler):
        if handler not in self._port.protocol.handlers:
            return
        self._port.protocol.handlers.remove(handler)

client=RepManager()
