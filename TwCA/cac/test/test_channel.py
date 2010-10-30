# -*- coding: utf-8 -*-

from twisted.internet import reactor

from zope.interface import implements

#from twisted.internet.base import DelayedCall
#DelayedCall.debug=True

from twisted.internet.defer import gatherResults, Deferred, \
                                   succeed, AlreadyCalledError
from twisted.internet.task import deferLater
from twisted.trial import unittest
from twisted.internet.protocol import ServerFactory

from TwCA.util.ca import CAmessage, padString, searchbody
from TwCA.util.twistedhelper import CAExpectProtocol, CAExpectDatagramProtocol
from TwCA.util.defs import CA_VERSION

from TwCA.cac.clichannel import CAClientChannel

from TwCA.cac.interfaces import IClient, IClientcircuit

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

    def __init__(self):
        self._mchan=None
        self._sent=[]
    
    def addchan(self, channel):
        self._mchan=channel

    def dropchan(self, channel):
        """Remove a channel from this circuit
        """
        assert channel is self._mchan

    def send(self, msg, dest=None):
        """Send a message to the client
        """
        self._sent.append((msg,dest))
        

class TestChannelBasic(unittest.TestCase):

    timeout=4

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

    def test_nocirc(self):
        """Lookup ok, circuit fails to connect
        """

        self.chan=CAClientChannel('somepv', self.cli)

        self.chan.whenCon.addCallback(lambda x:self.assertTrue(x is None))
        
        def whenWaiting():
            self.assertTrue(len(self.cli._L.callbacks), 1)
            self.assertTrue(self.cli._Lname == 'somepv')
            self.assertTrue(self.cli._Osrv is None)
            self.cli._L.callback(('localhost',42))
            self.cli._L=Deferred()

            self.assertTrue(len(self.cli._O.callbacks), 1)
            self.assertEqual(self.cli._Osrv, ('localhost',42))
            
            self.cli._O.callback(None)

            def waitAgain():
                self.assertTrue(len(self.cli._L.callbacks), 1)
                self.chan.close()
                self.cli._L.callback(None)
                del self.chan

            # wait for connection retry
            return deferLater(reactor, self.chan.reconnectDelay*1.1, waitAgain)


        return deferLater(reactor, self.chan.reconnectDelay*1.1, whenWaiting)

    def test_noattach(self):
        """Lookup and connect circuit, but fail to attach
        """

        self.chan=CAClientChannel('somepv', self.cli)

        self.chan.whenCon.addCallback(lambda x:self.assertTrue(x is None))
        
        circ=MockCircuit()

        self.cli._L.callback(('localhost',42))
        self.cli._O.callback(circ)

        def whenWaiting():
            #TODO: finish
            pass

        return deferLater(reactor, self.chan.reconnectDelay*1.1, whenWaiting)
