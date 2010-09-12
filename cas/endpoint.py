# -*- coding: utf-8 -*-

import asyncore, socket, logging
from util.udp import UDPdispatcher
from util.ca import CAmessage
import defs

log=logging.getLogger('cas.endpoint')

class CAcircuit(asyncore.dispatcher_with_send):
    
    def __init__(self, handler, sock=None, peer=None):
        self.handler=handler
        asyncore.dispatcher_with_send.__init__(self, sock)
        self.peer=peer
        self.in_buffer=''
        
        self.prio=0
        self.version=10
        self.user=None
        self.host=None
        
        self._circ={0 :self.caver,
                    20:self.caclient,
                    21:self.cahost}

        self.closeList=[]
        self.sids=set()

    def caver(self, pkt, x, y):
        log.debug('Create %s',self)
        self.version=pkt.count
        self.prio=pkt.dtype

    def caclient(self, pkt, x, y):
        self.user=pkt.body.strip('\0')
        log.debug('Update %s',self)
        self.circuitReady()

    def cahost(self, pkt, x, y):
        self.host=pkt.body.strip('\0')
        # do reverse lookup
        host, aliases, z = socket.gethostbyaddr(self.peer[0])
        if self.host!=host and self.host not in aliases:
            log.warning("""Rejecting connection from %s
            reverse lookup against %s failed""",self.peer[0],self.host)
            self.close()
            return
        log.debug('Update %s',self)
        self.circuitReady()

    def circuitReady(self):
        if self.user is None or self.host is None:
            return
        log.debug('Circuit ready')
        pkt=CAmessage(cmd=0, dtype=self.prio, count=defs.CA_VERSION)
        self.send(pkt.pack())

    def handle_connect(self):
        log.debug('Create %s',self)

    def handle_close(self):
        log.debug('Destroy %s',self)
        self.handler(None, self.peer, self)
        for c in self.closeList:
            c()
        self.close()
    
    def handle_read(self):
        msg = self.recv(8196)
        msg=self.in_buffer+msg

        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)
            
            hdl = self._circ.get(pkt.cmd, self.handler)
        
            hdl(pkt, self.peer, self)

        self.in_buffer=msg # save remaining

    def handle_error(self):
        raise

    def __str__(self):
        return 'Circuit v4%(version)d to %(peer)s as %(host)s:%(user)s'% \
            self.__dict__

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
        print 'Accepted from ',peer
        CAcircuit(self.handler, sock, peer)

    def handle_error(self):
        raise


class UDPpeer(UDPdispatcher):
    
    def __init__(self, handler, endpoint=('localhost',0)):
        self.handler=handler
        UDPdispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.set_reuse_addr()
        self.bind(endpoint)
        self.sbuf=[] # [(data,peer)]

    def handle_connect(self):
        pass

    def sendto(self, msg, peer):
        return self.sbuf.append((msg,peer))
    
    def writeable(self):
        return len(self.sbuf)>0

    def handle_write(self):
        if len(self.sbuf)==0:
            return
        msg, peer = self.sbuf[0]
        sent=UDPdispatcher.sendto(self,msg, peer)
        if sent == len(msg):
            self.sbuf.pop(0)
        else:
            print sent,len(msg)
            raise RuntimeError('send incomplete')

    def handle_read(self):
        msg, peer = self.recvfrom(4096)
        
        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)
        
            self.handler(pkt, peer, self)

        if len(msg)>0:
            print 'dropping incomplete message'

    def handle_error(self):
        raise
