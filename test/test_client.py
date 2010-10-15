# -*- coding: utf-8 -*-

from twisted.internet import reactor
from twisted.internet.defer import gatherResults
from twisted.trial import unittest
from twisted.protocols.loopback import loopbackTCP

from TwCA.util.config import Config
from TwCA.util.ca import CAmessage, padString, searchbody
from TwCA.util.twistedhelper import CAExpectProtocol, CAExpectDatagramProtocol
from TwCA.util.defs import CA_VERSION

from TwCA.cac.circuit import CAClientcircuit, CACircuitFactory
from TwCA.cac.resolver import Resolver
#from TwCA.cac.client import CAClient

testconfig=Config()
testconfig.sport=55064
testconfig.cport=55065

testconfig.addrs=[('127.0.0.1',testconfig.sport)]
testconfig.autoaddrs=False
testconfig.nameservs=[]

class TestCircuit(unittest.TestCase):
    
    timeout=1
    
    class StubClient:
        user='hello'
        host='world'
        def dispatch(self, pkt, _):
            self.fail('Unexpected package %s',pkt)
        
    class _CAClientcircuit(CAClientcircuit):
        # stop after version received
        def caver(self, pkt, endpoint):
            CAClientcircuit.caver(self,pkt,endpoint)
            self.transport.loseConnection()

    def test_handshakeV11(self):
        """Handshake with a v11 server.
        
        Server sends version after authentication
        """
        client=self.StubClient()
        
        user=padString('hello')
        host=padString('world')

        program= \
            [('recv',CAmessage(dtype=0, count=CA_VERSION)),
             ('recv',CAmessage(cmd=20, size=len(user), body=user)),
             ('recv',CAmessage(cmd=21, size=len(host), body=host)),
             ('send',CAmessage(dtype=0, count=11)),
            ]
        
        serv=CAExpectProtocol(self, program, halt=False)
        cli =self._CAClientcircuit(client)

        d=loopbackTCP(serv, cli, noisy=True)
        @d.addCallback
        def postCondition(value):
            self.assertEqual(len(serv.program),0)
            self.assertEqual(cli.version,11)
            return value

        return d

    def test_handshakeV13(self):
        """Handshake with a v11 server.
        
        Server sends version on connection
        to facilitate name server on TCP
        """
        client=self.StubClient()
        
        user=padString('hello')
        host=padString('world')

        program= \
            [('send',CAmessage(dtype=0, count=13)),
             ('recv',CAmessage(dtype=0, count=CA_VERSION)),
             ('recv',CAmessage(cmd=20, size=len(user), body=user)),
             ('recv',CAmessage(cmd=21, size=len(host), body=host)),
            ]
        
        serv=CAExpectProtocol(self, program, halt=False)
        cli =self._CAClientcircuit(client)

        d=loopbackTCP(serv, cli, noisy=True)
        @d.addCallback
        def postCondition(value):
            self.assertEqual(len(serv.program),0)
            self.assertEqual(cli.version,13)
            return value

        return d

class TestResolver(unittest.TestCase):
    
    def test_udplookup(self):
        name=padString('test1')

        serv=CAExpectDatagramProtocol(self, [], halt=False)

        up=reactor.listenUDP(0, serv, interface='127.0.0.1')

        addr=up.getHost()
        addr=addr.host, addr.port

        conf=Config(Config.empty)
        conf.addrs=[addr]
        
        resolv=Resolver(conf=conf)

        serv.dest='127.0.0.1', resolv._udp.getHost().port

        # name search
        # respond after second request
        serv.program= \
            [('recv',CAmessage(dtype=0, count=CA_VERSION)),
             ('recv',CAmessage(cmd=6, size=len(name),
                               dtype=5, count=CA_VERSION,
                               p1=0, p2=0, body=name)),
             ('recv',CAmessage(dtype=0, count=CA_VERSION)),
             ('recv',CAmessage(cmd=6, size=len(name),
                               dtype=5, count=CA_VERSION,
                               p1=0, p2=0, body=name)),
             ('send',CAmessage(cmd=6, size=8, dtype=addr[1],
                               p1=0xffffffff, p2=0,
                               body=searchbody.pack(11))),
            ]
        

        d=resolv.lookup('test1')

        @d.addCallback
        def result(srv):
            self.assertEqual(srv, addr)
            
            self.assertEqual(len(serv.program),0)

            d1=up.stopListening()
            d2=resolv.close()
            return gatherResults([d1,d2])

        return d
