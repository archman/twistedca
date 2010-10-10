# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('cac.partyline')

from time import time, ctime
from copy import copy
from socket import inet_ntoa, inet_aton

from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from TwCA.util.defs import SERVER_PORT
from TwCA.util.udp import SharedUDP
from TwCA.util.ifinspect import getifinfo

from TwCA.cas.endpoint import UDPpeer

from repclient import client

class IOC(object):
    
    def __init__(self, key, pkt):
        self.addr, self.ip, self.port = key
        self.next=(None,None)
        self.seen=[]
        now=time()

        self.time=ctime(now)
        self.seq=pkt.p1

        log.info('S %(time)s %(addr)s:%(port)u %(seq)u New IOC'%self.__dict__)
        if self.ip!=self.addr:
            log.info('  Advertising IP %s'%self.ip)

        self.update(pkt, ocr=now)

    def update(self, pkt, ocr=None):
        if ocr is None: ocr=time()

        cur = (pkt.p1, ocr)
        self.seen.append(cur)
        while len(self.seen)>10:
            self.seen.pop(0)

        if self.next == (None,None):
            self.next = (cur[0]+1, cur[1]+30.0)
            return

        next=self.next
        dts = map(lambda a,b:a[1]-b[1], self.seen[1:], self.seen[:-1])
        self.next=(cur[0]+1, ocr + sum(dts)/len(dts))

        self.time=ctime(ocr)
        self.seq=pkt.p1
        log.info('S %(time)s %(addr)s:%(port)u %(seq)u'%self.__dict__)

        dt = cur[1] - next[1]

        if next[0] != cur[0]:
            log.info('  Expect %u Recv %u'%(next[0], cur[0]))

        if next[0] > cur[0]:
            log.info('  Possible reboot')

        if abs(dt)>5.0:
            if dt>0:
                log.info('  Late %.2f'%dt)
            elif dt<0:
                log.info('  Early %.2f'%-dt)

    def drop(self, now):
        self.time=ctime(now)
        log.info('S %(time)s %(addr)s:%(port)u Drop'%self.__dict__)
        log.info('  No beacon in %.2f'%(now-self.seen[-1][1]))

    @property
    def key(self):
        return (self.addr, self.ip, self.port)

    @property
    def due(self):
        return self.seen[-1][1]

    @classmethod
    def makeKey(cls, src, pkt):
        return (src[0], inet_ntoa(inet_aton(str(pkt.p2))), pkt.dtype)

iocs={}

def beacon(pkt, peer):
    key = IOC.makeKey(peer, pkt)
    
    ioc=iocs.get(key)
    if ioc is None:
        ioc=IOC(key, pkt)
        iocs[key]=ioc
    else:
        ioc.update(pkt)

class Client(object):
    
    def __init__(key, pkt):
        self.addr, self.port = key
        self.last=None
        now=time()
        self.version=None

        self.time=ctime(now)

        log.info('C %(time)s %(addr)s:%(port)u New client'% \
                 self.__dict__)

        self.update(pkt, now)

    def update(self, pkt, ocr=None):
        if ocr is None: ocr=time()

        if self.last is not None:
            log.info('C %(time)s %(addr)s:%(port)u New client'% \
                    self.__dict__)

        self.last=ocr

        self.time=ctime(self.last)

        if ( pkt.cmd==0 or pkt.cmd==6 ) and self.version!=pkt.count:
            self.version=pkt.count
            log.info('  Protocol v4%u',self.version)

        if pkt.cmd==0:
            pass
        elif pkt.cmd==6:
            log.info('  Looking for %s',pkt.body.rstrip())
            if pkt.dtype!=5:
                log.info('  Invalid reply flag %u'%pkt.dtype)
        else:
            log.warning('C %(time)s %(addr)s:%(port)u Unusual message'%self.__dict__)
            log.warning('  %s',pkt)
            self.version=10

    def drop(self, now):
        self.time=ctime(now)
        log.info('C %(time)s %(addr)s:%(port)u Forget client'%self.__dict__)
        log.info('  No activity in %.2f'%(now-self.last))

clients={}

def bcast(pkt, peer, _):
    print 'received',pkt,'from',peer

    client=clients.get(peer)
    if client is None:
        client=Client(peer, pkt)
        clients[key]=client
    else:
        client.update(pkt)
    

def clean():
    now=time()

    for key, ioc in copy(iocs).iteritems():
        if now - ioc.due >= 130.0:
            iocs.pop(key)
            ioc.drop(now)

    for key, client in copy(clients).iteritems():
        if now - client.last >= 130.0:
            clients.pop(key)
            client.drop(now)

def main():
    client.add(beacon)
    cleaner=LoopingCall(clean)
    cleaner.start(130)

    bcasters=[]
    for intr in getifinfo():
        addr= intr.addr
        bp=SharedUDP(SERVER_PORT,UDPpeer(bcast),
                     addr)
        bp.startListening()
        host=bp.getHost()
        log.debug('Listening on %s:%u',host.host,host.port)

    reactor.run()
    
    cleaner.stop()
    
    for bp in bcasters:
        bp.stopListening()

    client.remove(beacon)

if __name__=='__main__':
    import logging
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    main()
