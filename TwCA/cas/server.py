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
    """Root server object.
    
    Listens on network interfaces, sends beacons,
    and connects to PVs.
    
    The base implementation keeps a list of PVs,
    but it is possible to replace the Lookup()
    and GetPV() methods for different behavior.
    """
    
    def __init__(self, conf=Config.default,
                 pvs=[], reactor=reactor):
        """Create a new CA server.
        
        A Config instance is used to control which
        network interfaces and ports are used.
        """
        self.reactor=reactor
        self.interfaces=[] # [(TCPEndpint, UDPPeer)]
        self.sport, self.cport=conf.sport, conf.cport

        self.tcpfactory=protocol.ServerFactory()
        self.tcpfactory.protocol=CAcircuit
        self.tcpfactory.server=self

        # fill beacon address list
        self.becdests=set()

        # each interface gets a TCP port (sport or a random assignment)
        # and a shared UDP port (always sport).
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

            # UDP port is given the port that the TCP listener
            # is bound to.
            up=SharedUDP(conf.sport,
                            UDPpeer(self.dispatchudp,bound.port),
                            interface=bound.host,
                            reactor=reactor)
            up.startListening()

            self.interfaces.append((tp,up))

            # broadcast on each capable interface giving
            # the TCP port that its listener is using.
            # TODO: this doesn't work for unicast.
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
        
        self.closeList=set() # actions to take when server is closed

        self.beaconID=0
        self.beaconWait=0.02 # initial beacon period
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
            tp.stopListening() # will cause active connections to close

    def sendBeacon(self):

        for dest, srv, sock in self.becdests:
            # Note that broadcast beacons include to full address
            # and do not depend on the repeater to determine them.
            # TODO: Is this correct?  What about unicast.
            b = CAmessage(cmd=13, dtype=srv.port,
                          p1=self.beaconID,
                          p2=addr2int(srv.host)).pack()

            try:
                sock.write(b, (dest, self.cport))
            except socket.error, e:
                #TODO: Why is this raising EINVAL for some bcast?
                #print repr(b), (intr, self.cport)
                pass

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
        if isinstance(ret, tuple) and pkt.count<11:
            # redirect not supported by older clients
            return

        elif ret and not isinstance(ret, tuple):
            ret = (0xffffffff, endpoint.tcpport)

        if ret:
            ack=CAmessage(cmd=6, size=8, dtype=ret[1],
                          p1=ret[0], p2=pkt.p2,
                          body=packSearchBody(CA_VERSION))

            endpoint.sendto(ack.pack(), peer)
            
        
    def Lookup(self,name):
        """Called in responce to name search requests.
        
        Can return either True/False, or a tuple of (ip, port).
        The ip returned must be a 32-bit integer (host order).
        """
        ret=name in self.pvs
        if ret:
            log.info('I have %s',name)
        return ret

    def GetPV(self,name):
        """Called when a client trys to create a channel
        
        Return a PV instance or None.
        """
        return self.pvs.get(name)
