# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('cac.partyline')

from time import time, ctime
from copy import copy
from socket import inet_ntoa, inet_aton

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from repclient import client

class IOC(object):
    
    def __init__(self, key, pkt):
        self.addr, self.ip, self.port = key
        self.next=(None,None)
        self.seen=[]
        now=time()

        self.time=ctime(now)
        self.seq=pkt.p1

        log.info('%(time)s %(addr)s:%(port)u %(seq)u New IOC'%self.__dict__)
        if self.ip!=self.addr:
            log.info('    Advertising IP %s'%self.ip)

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
        log.info('%(time)s %(addr)s:%(port)u %(seq)u'%self.__dict__)

        dt = cur[1] - next[1]

        if next[0] != cur[0]:
            log.info('    Expect %u Recv %u'%(next[0], cur[0]))

        if next[0] > cur[0]:
            log.info('    Possible reboot')

        if abs(dt)>5.0:
            if dt>0:
                log.info('    Late %.2f'%dt)
            elif dt<0:
                log.info('    Early %.2f'%-dt)

    def drop(self, now):
        self.time=ctime(now)
        log.info('%(time)s %(addr)s:%(port)u Drop'%self.__dict__)
        log.info('    No beacon in %.2f'%(now-self.seen[-1][1]))

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

def clean():
    now=time()

    for key, ioc in copy(iocs).iteritems():
        if now - ioc.due >= 130.0:
            iocs.pop(key)
            ioc.drop(now)

def main():
    client.add(beacon)
    cleaner=LoopingCall(clean)
    cleaner.start(130)

    reactor.run()
    
    cleaner.stop()
    client.remove(beacon)

if __name__=='__main__':
    import logging
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    main()
