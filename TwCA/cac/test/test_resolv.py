# -*- coding: utf-8 -*-

#import logging
#logging.basicConfig(format='%(message)s',level=logging.DEBUG)

from twisted.internet import reactor

#from twisted.internet.base import DelayedCall
#DelayedCall.debug=True

from twisted.internet.defer import gatherResults
from twisted.internet.task import deferLater
from twisted.trial import unittest
from twisted.internet.protocol import ServerFactory

from TwCA.util.config import Config
from TwCA.util.ca import CAmessage, padString, searchbody
from TwCA.util.twistedhelper import CAExpectProtocol, CAExpectDatagramProtocol
from TwCA.util.defs import CA_VERSION

from TwCA.cac.resolver import Resolver
from TwCA.cac.circuit import CACircuitFactory

class StubClient:
    user='hello'
    host='world'
    reactor=reactor
    tst=None
    def dispatch(self, pkt, _):
        self.tst.fail('Unexpected packet %s'%pkt)
    
class CAExpectFactory(ServerFactory):
    protocol=CAExpectProtocol
    tst=None
    program=None
    halt=False
    
    def buildProtocol(self, _):
        p=self.protocol(self.tst, self.program, self.halt)
        #p.debug=True
        return p

class TestResolver(unittest.TestCase):
    
    timeout=4

    def tearDown(self):
        ds=[]
        if hasattr(self, 'up'):
            ds.append(self.up.stopListening())
        if hasattr(self, 'cfact'):
            self.cfact.close()
        if hasattr(self, 'serv'):
            ds.append(self.serv.stopListening())
        if hasattr(self, 'resolv'):
            ds.append(self.resolv.close())
        return gatherResults(ds)

    def test_udpnoop(self):
        """Start up and shutdown without doing anything
        """

        conf=Config(Config.empty)
        conf.addrs=[('127.0.0.1', 1)] # will not be used
        
        resolv=Resolver(conf=conf)
        
        d1=resolv.lookup('junkname')
        @d1.addCallback
        def abort(name):
            self.assertTrue(name is None)
        
        d2=resolv.close()
        
        return gatherResults([d1,d2])

    def test_udpabort(self):
        """Abort in progress request
        """

        conf=Config(Config.empty)
        
        resolv=Resolver(conf=conf)
        
        d1=resolv.lookup('junkname')
        @d1.addCallback
        def abort(name):
            self.assertTrue(name is None)

        d2=deferLater(reactor, 0.5, resolv.close)
        
        return gatherResults([d1,d2])
    
    def test_udplookup(self):
        name=padString('test1')

        serv=CAExpectDatagramProtocol(self, [], halt=False)

        up=self.up=reactor.listenUDP(0, serv, interface='127.0.0.1')

        addr=up.getHost()
        addr=addr.host, addr.port

        conf=Config(Config.empty)
        conf.addrs=[addr]
        
        resolv=self.resolv=Resolver(conf=conf)

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


        return d

    def test_tcpnoop(self):
        client=StubClient()
        client.tst=self
        
        self.cfact=CACircuitFactory(client)

        conf=Config(Config.empty)
        conf.nameservs=[('127.0.0.1', 1)] # will not be used
        
        resolv=Resolver(conf=conf, tcpfactory=self.cfact)
        
        d1=resolv.lookup('junkname')
        @d1.addCallback
        def abort(name):
            self.assertTrue(name is None)
        
        d2=resolv.close()
        
        return gatherResults([d1,d2])
    
    def test_tcpabort(self):
        """Abort a TCP persistent circuit
        """
        client=StubClient()
        client.tst=self

        name1=padString('test1')
        user=padString('hello')
        host=padString('world')

        sfact=self.sfact=CAExpectFactory()
        sfact.tst=self
            
        self.serv=reactor.listenTCP(0, sfact, interface='127.0.0.1')
        target=('127.0.0.1', self.serv.getHost().port)

        sfact.program= \
            [('send',CAmessage(dtype=0, count=12)),
             ('recv',CAmessage(dtype=0, count=CA_VERSION)),
             ('recv',CAmessage(cmd=20, size=len(user), body=user)),
             ('recv',CAmessage(cmd=21, size=len(host), body=host)),
            ]+[('recv',CAmessage(cmd=6, size=len(name1),
                               dtype=5, count=CA_VERSION,
                               p1=0, p2=0, body=name1))]*6
        
        self.cfact=CACircuitFactory(client)

        conf=Config(Config.empty)
        conf.nameservs=[target]
        
        resolv=Resolver(conf=conf, tcpfactory=self.cfact)
        

        d=resolv.lookup('test1')

        @d.addCallback
        def result(srv):
            self.assertTrue(srv is None)

        d2=deferLater(reactor, 0.5, resolv.close)

        return gatherResults([d,d2])

    
    def test_tcplookup(self):
        client=StubClient()
        client.tst=self

        name1=padString('test1')
        name2=padString('anotherpv')
        user=padString('hello')
        host=padString('world')

        sfact=self.sfact=CAExpectFactory()
        sfact.tst=self
            
        self.serv=reactor.listenTCP(0, sfact, interface='127.0.0.1')
        target=('127.0.0.1', self.serv.getHost().port)

        sfact.program= \
            [('send',CAmessage(dtype=0, count=12)),
             ('recv',CAmessage(dtype=0, count=CA_VERSION)),
             ('recv',CAmessage(cmd=20, size=len(user), body=user)),
             ('recv',CAmessage(cmd=21, size=len(host), body=host)),
             ('recv',CAmessage(cmd=6, size=len(name1),
                               dtype=5, count=CA_VERSION,
                               p1=0, p2=0, body=name1)),
             ('send',CAmessage(cmd=6, size=8, dtype=target[1],
                               p1=0xffffffff, p2=0,
                               body=searchbody.pack(12))),
             ('recv',CAmessage(cmd=6, size=len(name2),
                               dtype=5, count=CA_VERSION,
                               p1=1, p2=1, body=name2)),
             ('send',CAmessage(cmd=6, size=8, dtype=target[1],
                               p1=0xffffffff, p2=1,
                               body=searchbody.pack(12))),
            ]
        
        self.cfact=CACircuitFactory(client)

        conf=Config(Config.empty)
        conf.nameservs=[target]
        
        resolv=self.resolv=Resolver(conf=conf, tcpfactory=self.cfact)
        

        d=resolv.lookup('test1')

        @d.addCallback
        def result(srv):
            self.assertEqual(srv, target)
            
            self.assertEqual(len(self.sfact.program),2)
            
            return resolv.lookup('anotherpv')

        @d.addCallback
        def result(srv):
            self.assertEqual(srv, target)
            
            self.assertEqual(len(self.sfact.program),0)

        return d
    
    def test_tcpnoserv(self):
        """Abort a TCP persistent circuit trying to connect to nothing
        """
        client=StubClient()
        client.tst=self

        name1=padString('test1')
        user=padString('hello')
        host=padString('world')

        target=('127.0.0.1', 65534)
        
        self.cfact=CACircuitFactory(client)

        conf=Config(Config.empty)
        conf.nameservs=[target]
        
        resolv=Resolver(conf=conf, tcpfactory=self.cfact)
        

        d=resolv.lookup('test1')

        @d.addCallback
        def result(srv):
            self.assertTrue(srv is None)

        d2=deferLater(reactor, 0.5, resolv.close)

        return gatherResults([d,d2])
