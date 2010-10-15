# -*- coding: utf-8 -*-

from twisted.trial import unittest
from twisted.protocols.loopback import loopbackTCP

from TwCA.util.config import Config
from TwCA.util.ca import CAmessage, padString
from TwCA.util.twistedhelper import CAProtocol
from TwCA.util.defs import CA_VERSION

from TwCA.cac.circuit import CAClientcircuit, CACircuitFactory
#from TwCA.cac.resolver
#from TwCA.cac.client import CAClient

testconfig=Config()
testconfig.sport=55064
testconfig.cport=55065

testconfig.addrs=[('127.0.0.1',testconfig.sport)]
testconfig.autoaddrs=False
testconfig.nameservs=[]

class TestServerCircuit(CAProtocol):
    
    def __init__(self, tst, v13=False):
        self.tst, self.v13=tst, v13
        user=padString('hello')
        host=padString('world')

        self.needed=set([0,20,21])
        self._dispatch_table={
             0:self.expect(CAmessage(dtype=0, count=CA_VERSION)),
            20:self.expect(CAmessage(cmd=20, size=len(user), body=user)),
            21:self.expect(CAmessage(cmd=21, size=len(host), body=host)),
            }

        if v13:
            self.next=lambda:None
        else:
            self.next=self.sendVersion

    def connectionMade(self):
        if self.v13:
            self.sendVersion()

    def expect(self, epkt):
        
        def inspector(pkt, _):
            self.tst.assertEqual(pkt.cmd,  epkt.cmd)
            self.tst.assertEqual(pkt.size, epkt.size)
            self.tst.assertEqual(pkt.dtype,epkt.dtype)
            self.tst.assertEqual(pkt.count,epkt.count)
            self.tst.assertEqual(pkt.p1,   epkt.p1)
            self.tst.assertEqual(pkt.p2,   epkt.p2)
            self.tst.assertEqual(pkt.body ,epkt.body)
            self.needed.remove(pkt.cmd)
            if len(self.needed)==0:
                self.next()
        return inspector

    def sendVersion(self):
        if self.v13:
            self.tst.assertTrue(len(self.needed),3)
        msg=CAmessage(dtype=0, count=11).pack()
        self.transport.write(msg)

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
        
        serv=TestServerCircuit(self, False)
        cli =self._CAClientcircuit(client)

        d=loopbackTCP(serv, cli, noisy=True)
        @d.addCallback
        def postConditions(result):
            self.assertEqual(len(serv.needed),0)
            return result

        return d

    def test_handshakeV13(self):
        """Handshake with a v11 server.
        
        Server sends version on connection
        to facilitate name server on TCP
        """
        client=self.StubClient()
        
        serv=TestServerCircuit(self, True)
        cli =self._CAClientcircuit(client)

        d=loopbackTCP(serv, cli, noisy=True)
        @d.addCallback
        def postConditions(result):
            self.assertEqual(len(serv.needed),0)
            return result

        return d

class TestClient(unittest.TestCase):
    
    def test_noop(self):
        pass
