# -*- coding: utf-8 -*-

#import logging
#logging.basicConfig(format='%(message)s',level=logging.DEBUG)

from twisted.internet import reactor

from zope.interface import implements

#from twisted.internet.base import DelayedCall
#DelayedCall.debug=True

from twisted.internet.defer import gatherResults, Deferred, \
                                   succeed, AlreadyCalledError, \
                                   inlineCallbacks
from twisted.internet.task import deferLater
from twisted.trial import unittest
from twisted.internet.protocol import ServerFactory

from TwCA.util.ca import CAmessage, padString, searchbody
from TwCA.util.twistedhelper import CAExpectProtocol, CAExpectDatagramProtocol
from TwCA.util.defs import CA_VERSION

from TwCA.cac.clichannel import CAClientChannel

from TwCA.cac.interfaces import IClient, IClientcircuit
from TwCA.util.interfaces import IConnectNotify

class Counter(object):
    def __init__(self, c=0):
        self.c=c

class MockClient(object):
    
    implements(IClient)

    reactor = reactor
    user="testuser"
    host="testhost"
    
    def __init__(self):
        self.reset()

    def reset(self):
        self._L=Deferred()
        self._Lname=None
        self._O=Deferred()
        self._Osrv=None
        self._Rx=[]
        self.closeList=set()
    
    def close(self):
        pass

    def lookup(self,name):
        self._Lname=name
        return self._L

    def openCircuit(self,srv):
        self._Osrv=srv
        return self._O

    def dispatch(self,pkt, endpoint, peer=None):
        self._Rx.append((pkt,endpoint,peer))

class MockCircuit(object):
    
    implements(IClientcircuit)

    class MockConnector(object):
        implements(IConnectNotify)
        def __init__(self):
            self.whenCon=Deferred()
            self.whenDis=Deferred()
            self.whenDis.callback(None)

        def doCon(self, circ):
            self.whenDis=Deferred()
            self.whenCon.callback(circ)

        def doFail(self):
            d, self.whenCon = self.whenCon, Deferred()
            d.callback(None)

        def doLost(self, circ):
            self.whenCon=Deferred()
            d, self.whenDis = self.whenDis, Deferred()
            if circ is not None:
                d.callback(circ)

    class MockTransport(object):
        def __init__(self):
            self.connector=MockCircuit.MockConnector()

    def __init__(self):
        self._mchan=None
        self._sent=[]
        self.reqAttach=Deferred()
        self.transport=self.MockTransport()

    def addchan(self, channel):
        self._mchan=channel
        self.reqAttach.callback(channel)

    def dropchan(self, channel):
        """Remove a channel from this circuit
        """
        assert channel is self._mchan

    def send(self, msg, dest=None):
        """Send a message to the client
        """
        self._sent.append((msg,dest))

class TestChannelFail(unittest.TestCase):

    timeout=2

    def setUp(self):        
        self.cli=MockClient()

    def tearDown(self):
        if hasattr(self, 'chan'):
            self.chan.close()

    def test_noop(self):
        """Startup and shutdown before running reactor
        """
        self.chan=CAClientChannel('testpv', self.cli)

        c=Counter()

        @self.chan.whenDis.addCallback
        def onCon(chan):
            self.assertTrue(chan is self.chan)
            c.c+=2

        self.assertEqual(c.c, 2)

        @self.chan.whenCon.addCallback
        def onCon(chan):
            self.assertTrue(chan is None)
            c.c+=1

        self.assertEqual(self.cli.closeList, set([self.chan.close]))

        self.chan.close()
        del self.chan

        self.assertEqual(c.c, 3)
        self.assertTrue(self.cli._Lname is None)
        self.assertTrue(self.cli._Osrv is None)

    def test_nolookup(self):
        """Lookup fails
        """

        self.chan=CAClientChannel('testpv', self.cli)

        self.chan.whenCon.addCallback(lambda x:self.assertTrue(x is None))

        self.assertEqual(self.cli.closeList, set([self.chan.close]))
        
        def whenWaiting():
            self.assertTrue(len(self.cli._L.callbacks), 1)
            self.assertTrue(self.cli._Lname == 'testpv')
            self.assertTrue(self.cli._Osrv is None)
            self.chan.close()
            del self.chan
            self.cli._L.callback(None)

        # wait for first connection attempt
        return deferLater(reactor, self.chan.reconnectDelay*1.1, whenWaiting)

    def test_lookupabort(self):
        """Lookup ok, close before circuit connects
        """

        self.chan=CAClientChannel('missingpv', self.cli)

        self.chan.whenCon.addCallback(lambda x:self.assertTrue(x is None))
        
        def whenWaiting():
            self.assertTrue(len(self.cli._L.callbacks), 1)
            self.assertTrue(self.cli._Lname == 'missingpv')
            self.cli._L.callback(('localhost',42))
            self.cli._L=succeed(None)

            self.assertTrue(len(self.cli._O.callbacks), 1)
            self.assertEqual(self.cli._Osrv, ('localhost',42))

            self.chan.close()
            del self.chan

        return deferLater(reactor, self.chan.reconnectDelay*1.1, whenWaiting)

    @inlineCallbacks
    def test_nocirc(self):
        """Lookup ok, circuit fails to connect
        """

        self.chan=CAClientChannel('somepv', self.cli)

        self.chan.whenCon.addCallback(lambda x:self.assertTrue(x is None))
        
        # wait for connection attempt
        yield deferLater(reactor, self.chan.reconnectDelay*1.1, lambda:None)

        # ensure channel initiated lookup
        self.assertTrue(len(self.cli._L.callbacks), 1)
        self.assertTrue(self.cli._Lname == 'somepv')
        self.assertTrue(self.cli._Osrv is None)

        self.cli._L.callback(('localhost',42))
        self.cli._L=Deferred()

        # ensure channel requested a channel
        self.assertTrue(len(self.cli._O.callbacks), 1)
        self.assertEqual(self.cli._Osrv, ('localhost',42))

        # fail channel request
        self.cli._O.callback(None)

        # wait for connection retry
        yield deferLater(reactor, self.chan.reconnectDelay*1.1, lambda:None)

        self.assertTrue(len(self.cli._L.callbacks), 1)

        # simulate client close()
        self.chan.close()
        self.cli._L.callback(None)

        del self.chan


    def test_noattach(self):
        """Lookup and connect circuit, but disconnect before attach
        """

        self.chan=CAClientChannel('somepv', self.cli)

        self.chan.whenCon.addCallback(lambda x:self.assertTrue(x is None))
        
        circ=MockCircuit()
        circ.transport.connector.doCon(circ)

        self.cli._L.callback(('localhost',42))
        self.cli._O.callback(circ)
        
        @circ.reqAttach.addCallback
        def onAttach(chan):
            self.assertEqual(chan, self.chan)
            self.assertEqual(chan.state, chan.S_attach)

            self.assertTrue(chan._d is not None)
            circ.transport.connector.doLost(circ)
            self.assertTrue(chan._d is None)

            self.assertEqual(self.chan.state, self.chan.S_init)
            self.chan.close()

        return circ.reqAttach

    def test_nochan(self):
        """Lookup and connect circuit, but server does not have channel
        """

        self.chan=CAClientChannel('somepv', self.cli)

        self.chan.whenCon.addCallback(lambda x:self.assertTrue(x is None))
        
        circ=MockCircuit()
        circ.transport.connector.doCon(circ)

        self.cli._L.callback(('localhost',42))
        self.cli._O.callback(circ)
        
        @circ.reqAttach.addCallback
        def onAttach(chan):
            self.assertEqual(chan, self.chan)
            self.assertEqual(chan.state, chan.S_attach)

            self.assertTrue(chan._d is not None)
            self.chan.dispatch(CAmessage(cmd=26), circ)
            self.assertTrue(chan._d is None)

            self.assertEqual(self.chan.state, self.chan.S_init)
            self.chan.close()

        return circ.reqAttach

class TestChannelConnect(unittest.TestCase):

    timeout=2

    def setUp(self):        
        self.cli=MockClient()

    def tearDown(self):
        if hasattr(self, 'chan'):
            self.chan.close()

    @inlineCallbacks
    def test_reconn(self):
        """connect, disconnect, and reconnect
        """

        self.chan=CAClientChannel('somepv', self.cli)

        cb=Counter()

        def conCB(chan, status):
            if status:
                cb.c+=5
            else:
                cb.c-=1
        self.chan.status.add(conCB)


        circ=MockCircuit()
        circ.transport.connector.doCon(circ)

        self.cli._L.callback(('localhost',42))
        self.cli._O.callback(circ)

        # wait until channel calls circ.addchan(chan)
        chan=yield circ.reqAttach

        self.assertEqual(chan, self.chan)
        self.assertEqual(chan.state, chan.S_attach)

        self.assertTrue(chan._d is not None)

        # fall out of circ.addchan(chan)
        # before sending packets
        yield deferLater(reactor, 0, lambda:None)

        # send rights
        self.chan.dispatch(
            CAmessage(cmd=22, p2=3), circ)
        # send channel create ok
        self.chan.dispatch(
            CAmessage(cmd=18, dtype=6, count=10, p2=52), circ)

        self.assertTrue(chan._d is None)

        # verify decode
        self.assertEqual(chan.rights, 3)
        self.assertEqual(chan.sid, 52)
        self.assertEqual((chan.dbr, chan.maxcount), (6, 10))

        self.assertEqual(self.chan.state, self.chan.S_connect)

        # wait for channel to signal connected
        chan=yield self.chan.whenCon

        # check that status callback was fired
        self.assertEqual(cb.c, 5)

        # prepare to drop circuit
        circ2=MockCircuit()
        circ2.transport.connector.doCon(circ2)

        self.cli._L=succeed(('localhost',43))
        self.cli._O=succeed(circ2)

        circ.transport.connector.doLost(circ)

        # wait for channel to signal disconnected
        chan=yield self.chan.whenDis

        self.assertEqual(chan.state, chan.S_init)
        # verify decode
        self.assertEqual(chan.rights, 0)
        self.assertEqual(chan.sid, None)
        self.assertEqual((chan.dbr, chan.maxcount), (None, 0))

        # check the status cb was notified of dcnt
        self.assertEqual(cb.c, 4)

        # wait until channel reattaches
        chan=yield circ2.reqAttach
        self.assertEqual(self.chan, chan)
        self.assertEqual(chan._circ, circ2)

        self.assertEqual(chan.state, chan.S_attach)

        self.assertTrue(chan._d is not None)

        # fall out of circ.addchan(chan)
        yield deferLater(reactor, 0, lambda:None)

        # send rights
        self.chan.dispatch(
            CAmessage(cmd=22, p2=2), circ2)
        # send channel create ok
        self.chan.dispatch(
            CAmessage(cmd=18, dtype=5, count=11, p2=53), circ2)

        # verify decode
        self.assertEqual(chan.rights, 2)
        self.assertEqual(chan.sid, 53)
        self.assertEqual((chan.dbr, chan.maxcount), (5, 11))

        self.assertEqual(self.chan.state, self.chan.S_connect)

        # wait for channel to signal connected
        chan=yield self.chan.whenCon

        # check that status callback was fired
        self.assertEqual(cb.c, 9)

        self.chan.close()

