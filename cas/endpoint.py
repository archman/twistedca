# -*- coding: utf-8 -*-

import asyncore, socket
from util.udp import UDPdispatcher
from util.ca import CAmessage

class CAendpoint(asyncore.dispatcher):
    
    def __init__(self, sock=None, peer=None):
        asyncore.dispatcher.__init__(self, sock)
        self.peer=peer

class TCPserver(asyncore.dispatcher):
    
    def __init__(self, handler, endpoint=('localhost',0)):
        self.handler=handler
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(endpoint)
        self.listen(5)
        
        print 'I am',self.socket.getsockname()

    def handle_accept(self):
        sock, peer = self.accept()
        print 'Connection from ',peer
        self.handler(sock, peer)


class UDPpeer(UDPdispatcher):
    
    def __init__(self, endpoint=('localhost',0)):
        UDPdispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(endpoint)
        self.sbuf=[] # [(data,peer)]

    def handle_connect(self):
        pass
    
    def writeable(self):
        return len(self.sbuf)>0

    def handle_write(self):
        if len(self.sbuf)==0:
            return
        msg, peer = self.sbuf[0]
        if self.sendto(msg, peer) == len(msg):
            self.sbuf.pop(0)
        else:
            print 'send failed'

    def handle_read(self):
        msg, peer = self.recvfrom(4096)
        
        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)
        
            print 'from',peer,':',pkt
        
            if pkt.cmd==1:
                print 'Client version',pkt.count
            
            elif pkt.cmd==6:
                print 'Looking for ',pkt.body

    def handle_error(self):
        raise
