# -*- coding: utf-8 -*-

from twisted.internet import reactor

#from twisted.internet.base import DelayedCall
#DelayedCall.debug=True

from twisted.internet.defer import gatherResults
from twisted.trial import unittest
from twisted.internet.protocol import ServerFactory
from twisted.protocols.loopback import loopbackTCP

from TwCA.util.ca import CAmessage, padString
from TwCA.util.twistedhelper import CAExpectProtocol
from TwCA.util.defs import CA_VERSION

from TwCA.cac.circuit import CAClientcircuit, CACircuitFactory

class StubClient:
    user='hello'
    host='world'
    reactor=reactor
    def dispatch(self, pkt, _):
        self.fail('Unexpected packet %s',pkt)


class TestCircuit(unittest.TestCase):
    
    timeout=1
        
    class _CAClientcircuit(CAClientcircuit):
        # stop after version received
        def caver(self, pkt, endpoint):
            CAClientcircuit.caver(self,pkt,endpoint)
            self.transport.loseConnection()

    def test_handshakeV11(self):
        """Handshake with a v11 server.
        
        Server sends version after authentication
        """
        client=StubClient()
        
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
        client=StubClient()
        
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


class TestCircuitFactory(unittest.TestCase):
    
    timeout=5
    
    class CAExpectFactory(ServerFactory):
        protocol=CAExpectProtocol
        tst=None
        program=None
        halt=False
        
        def buildProtocol(self, _):
            return self.protocol(self.tst, self.program, self.halt)
    
    def setUp(self):
        client=StubClient()
        
        user=padString('hello')
        host=padString('world')
        
        self.program = \
            [('send',CAmessage(dtype=0, count=13)),
             ('recv',CAmessage(dtype=0, count=CA_VERSION)),
             ('recv',CAmessage(cmd=20, size=len(user), body=user)),
             ('recv',CAmessage(cmd=21, size=len(host), body=host)),
            ]

        sfact=self.CAExpectFactory()
        sfact.tst=self
        sfact.program=self.program+self.program
            
        self.serv=reactor.listenTCP(0, sfact, interface='127.0.0.1')
        self.target=('127.0.0.1', self.serv.getHost().port)
        
        self.cfact=CACircuitFactory(client)

    def tearDown(self):
        self.cfact.close()
        return self.serv.loseConnection()
        
    def test_connect(self):
        """Test connect -> disconnect -> manual re-connect
        """
        d1=self.cfact.requestCircuit(self.target)
        d2=self.cfact.requestCircuit(self.target)
        
        self.assertEqual(len(self.cfact.circuits), 1)
        
        cc=self.cfact.circuits.values()[0]
        self.assertFalse(cc._DeferredConnector__C._DeferredManager__done)

        self.assertTrue(d1 is not d2)
        
        def onConnect(circ):
            self.failIfIdentical(circ, None, 'Connection failed')
            self.assertIsInstance(circ, CAClientcircuit)

            d=circ.transport.connector.whenDis
            
            circ.transport.loseConnection()

            return d

        d1.addCallback(onConnect)
        d2.addCallback(onConnect)
        
        def onDisconnect(circ):
            self.assertTrue(isinstance(circ, CAClientcircuit))
            self.assertEqual(len(self.program),4)
            
            return self.cfact.requestCircuit(self.target)

        d1.addCallback(onDisconnect)
        d2.addCallback(onDisconnect)

        d=gatherResults([d1, d2])
        @d.addCallback
        def onReconnect(circs):
            self.assertEqual(len(circs), 2)
            c1, c2 = circs
            self.assertTrue(c1 is c2)
            
            # circuit will be closed during cleanup

        return d

    def test_persist(self):
        """Test persistent circuits
        
        Used for TCP name servers
        """
        self.cfact.timeout=1

        d=self.cfact.requestCircuit(self.target, persist=True)
        
        class Counter(object):
            v=0
        C=Counter()

        @d.addCallback
        def conn(circ):
            self.failIfIdentical(circ, None, 'Connection failed')
            self.assertIsInstance(circ, CAClientcircuit)

            d=circ.transport.connector.whenDis

            circ.transport.loseConnection()
            C.v+=1
            
            return d

        @d.addCallback
        def dis(circ):
            # reconnection is automatic,
            # but we need to re-subscribe
            d=circ.transport.connector.whenCon
            C.v+=1
            return d

        @d.addCallback
        def recon(circ):
            self.assertEqual(C.v, 2)

        return d

    def test_noconnect(self):
        self.cfact.timeout=1

        host, port = self.target
        failtarget=(host, port+1) # assumed to not be a ca server

        d=self.cfact.requestCircuit(failtarget)

        @d.addCallback
        def con(circ):
            self.assertTrue(circ is None)

        return d
