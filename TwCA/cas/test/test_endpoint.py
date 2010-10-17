# -*- coding: utf-8 -*-

#import logging
#logging.basicConfig(format='%(message)s',level=logging.DEBUG)

from twisted.internet import reactor

from zope.interface import implements

#from twisted.internet.base import DelayedCall
#DelayedCall.debug=True

from twisted.internet.defer import gatherResults, Deferred
from twisted.internet.task import deferLater
from twisted.trial import unittest
from twisted.internet.protocol import ClientFactory
from twisted.internet.tcp import Connector

from TwCA.util.config import Config
from TwCA.util.ca import CAmessage, padString, searchbody
from TwCA.util.twistedhelper import CAExpectProtocol
from TwCA.util.defs import CA_VERSION

from TwCA.cas.interfaces import ICAServer
from TwCA.cas.endpoint import CAcircuit, CAServerCircuitFactory

class CAExpectFactory(ClientFactory):
    protocol=CAExpectProtocol
    tst=None
    program=None
    halt=False
    
    def buildProtocol(self, _):
        p=self.protocol(self.tst, self.program, self.halt)
        #p.debug=True
        return p

class TestFactory(CAServerCircuitFactory):
    
    def __init__(self, server):
        CAServerCircuitFactory.__init__(self, server)
        
        self.created=Deferred()

    def buildProtocol(self, x):
        p=CAServerCircuitFactory.buildProtocol(self, x)
        c, self.created = self.created, Deferred()
        c.callback(p)
        return p

def hookAction(d, k, key):
    defer=Deferred()
    old=d[k]
    def act(*args, **kws):
        ret=old(*args, **kws)
        defer.callback(key)
        return ret
    d[k]=act
    return defer

def insertAction(d, k, val):
    defer=Deferred()
    def act(*args, **kws):
        defer.callback((val,args,kws))
    d[k]=act
    return defer

class TestServer(object):
    implements(ICAServer)
    
    tst=None

    def __init__(self):
        self.pvs={}
        self.circuits=set()
    
    def Lookup(name):
        raise NotImplementedError('Lookup not implemented')

    def GetPV(self,name):
        return self.pvs[name]

    def dispatch(self, pkt, endpoint, peer=None):
        self.tst.fail('unexpected packet %s',pkt)


class TestServerCircuit(unittest.TestCase):
    
    timeout=2
    
    def setUp(self):
        self.server=TestServer()
        self.server.tst=self

        self.sfact=TestFactory(self.server)

        self.sport=reactor.listenTCP(0, self.sfact, interface='127.0.0.1')

        self.cfact=CAExpectFactory()

        self.cport=Connector('127.0.0.1', self.sport.getHost().port,
                             self.cfact, timeout=1,
                             bindAddress=None,
                             reactor=reactor)

    def tearDown(self):
        self.cport.disconnect()
        self.sport.loseConnection()

    def test_handshakev12(self):
        user=padString('hello')
        host=padString('world')

        self.cfact.tst=self
        self.cfact.program = \
            [('recv',CAmessage(dtype=0, count=CA_VERSION)),
             ('send',CAmessage(dtype=0, count=10)),
             ('send',CAmessage(cmd=20, size=len(user), body=user)),
             ('send',CAmessage(cmd=21, size=len(host), body=host)),
            ]

        d=self.sfact.created

        @d.addCallback
        def initial(circ):
            self.assertIsInstance(circ, CAcircuit)
            self.savecirc=circ
            
            d1=hookAction(circ._circ, 21, circ)
            d2=circ.whenCon
            return gatherResults([d1,d1])

        @d.addCallback
        def done(_):
            circ=self.savecirc
            self.assertEqual(self.cfact.program, [])
            self.assertIsInstance(circ, CAcircuit)
            self.assertEqual(circ.user, 'hello')
            self.assertEqual(circ.host, '<ANONYMOUS>')
            self.assertEqual(circ.version, 10)
            self.assertEqual(circ.prio, 0)

        self.cport.connect()

        return d
