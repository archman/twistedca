# -*- coding: utf-8 -*-

import logging, socket
log=logging.getLogger('cas.server')
from errno import EPERM, EINVAL, ENETUNREACH
from socket import inet_aton

from twisted.internet import reactor,tcp,protocol
from twisted.internet.task import LoopingCall
from twisted.internet.error import CannotListenError

from TwCA.util.ca import CAmessage, packSearchBody
from TwCA.util.udp import SharedUDP, addr2int
from TwCA.util.defs import *
from TwCA.util.config import Config
from TwCA.util.ifinspect import getifinfo

from endpoint import UDPpeer, CAcircuit

from struct import Struct

class Server(object):
    
    def __init__(self, conf=Config.default,
                 pvs=[], reactor=reactor):
        self.reactor=reactor
        self.interfaces=[]
        self.sport, self.cport=conf.sport, conf.cport

        self.tcpfactory=protocol.ServerFactory()
        self.tcpfactory.protocol=CAcircuit
        self.tcpfactory.server=self

        # fill beacon address list
        self.becdests=set()

        for intr in getifinfo():
            if not conf.srvautoaddrs and \
                    (intr.addr not in conf.srvaddrs or \
                     intr.addr in conf.srvignoreaddrs):
                continue


            try:
                tp=reactor.listenTCP(self.sport,
                                    self.tcpfactory,
                                    interface=intr.addr)
            except CannotListenError:
                # if the requested port is in use
                # fall back to another
                tp=reactor.listenTCP(0,
                                    self.tcpfactory,
                                    interface=intr.addr)
                tcpport=tp.getHost().port
                log.warning('Server running on non-standard port %d on %s',
                            tcpport, intr.addr)

            bound=tp.getHost()

            log.info('Server bind to %s',bound)

            up=SharedUDP(conf.sport,
                            UDPpeer(self.dispatchudp,bound.port),
                            interface=bound.host,
                            reactor=reactor)
            up.startListening()

            self.interfaces.append((tp,up))

            if intr.broadcast is not None and \
                    (conf.beaconautoaddrs or \
                     intr.broadcast in conf.beaconaddrs):
                log.debug('Beacons to %s',intr.broadcast)
                self.becdests.add((intr.broadcast,bound,up))


        self._udp={0:self.ignore,6:self.nameres}
        self._tcp={6:self.nameres}

        self.pvs={}
        for pv in pvs:
            self.pvs[pv.name]=pv
        
        self.closeList=set()

        self.beaconID=0
        self.beaconWait=0.02
        reactor.callLater(self.beaconWait,self.sendBeacon)

    def close(self):
        from copy import copy
        # make a copy of the list (not contents)
        # because calling c() may cause the size
        # of closeList to change
        for c in copy(self.closeList):
            c()

        for tp, up in self.interfaces:
            up.stopListening()
            tp.stopListening()

    def sendBeacon(self):

        for dest, srv, sock in self.becdests:
            b = CAmessage(cmd=13, dtype=srv.port,
                          p1=self.beaconID,
                          p2=addr2int(srv.host)).pack()

            # Interface address will be added by receiving
            # CA repeater
            #b.p2=addr2int(host.host)

            try:
                sock.write(b, (dest, self.cport))
            except socket.error, e:
                #TODO: Why is this raising EINVAL for some bcast?
                #print repr(b), (intr, self.cport)
                if e.errno not in (EPERM, EINVAL, ENETUNREACH):
                    raise

        self.beaconID=self.beaconID+1
        if self.beaconWait<30:
            self.beaconWait=min(self.beaconWait*2.0, 30)
        reactor.callLater(self.beaconWait,self.sendBeacon)

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
        print '>> Unknown <<',peer,'sent',pkt

    def nameres(self, pkt, peer, endpoint):
        name=pkt.body.strip('\0')
        log.info('%s is looking for %s',str(peer),name)
        ret = self.Lookup(name)
        if ret and not isinstance(ret, tuple):
            ret = (0xffffffff, endpoint.tcpport)
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
