# -*- coding: utf-8 -*-

import asyncore, socket, logging
from util.udp import UDPdispatcher
from util.ca import CAmessage
from channel import Channel
import defs
from copy import copy

log=logging.getLogger('cas.endpoint')

class CAcircuit(asyncore.dispatcher_with_send):
    
    def __init__(self, server, sock=None, peer=None):
        self.server=server
        asyncore.dispatcher_with_send.__init__(self, sock)
        self.peer=peer
        self.in_buffer=''
        
        self.prio=0
        self.version=10
        self.user=None
        self.host=None
        
        self._circ={0 :self.caver,
                    1 :self.forwardchan,
                    2 :self.forwardchan,
                    4 :self.forwardchan,
                    12:self.clearchan,
                    15:self.forwardchan,
                    18:self.createchan,
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

    def handle_connect(self):
        log.debug('Create %s',self)

    def handle_close(self):
        log.debug('Destroy %s',self)
        self.close()
        
        self.server.dispatchtcp(None, self.peer, self)
        # make a copy of the list (not contents)
        # because calling c() may cause the size
        # of closeList to change
        for c in copy(self.closeList):
            c()
    
    def handle_read(self):
        msg = self.recv(8196)
        msg=self.in_buffer+msg

        while msg is not None and len(msg)>=16:
        
            pkt, msg = CAmessage.unpack(msg)
            
            hdl = self._circ.get(pkt.cmd, self.server.dispatchtcp)
        
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
