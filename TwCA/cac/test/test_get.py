# -*- coding: utf-8 -*-

#import logging
#logging.basicConfig(format='%(message)s',level=logging.DEBUG)
from weakref import ref

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

from TwCA.util.defs import *
from TwCA.util.ca import CAmessage, padString, searchbody
from TwCA.util.idman import IDManager, DeferredManager

from TwCA.cac.interfaces import IChannel, IClientcircuit
from TwCA.util.interfaces import IConnectNotify

from TwCA.cac.get import CAGet

class Counter(object):
    def __init__(self, c=0):
        self.c=c

class MockCircuit(object):
    
    implements(IClientcircuit)

    def __init__(self):
        self.pendingActions=IDManager()
        self.subscriptions=IDManager()
        self._sent=[]

    version=0

    def addchan(self,channel):
        pass

    def dropchan(self,channel):
        pass

    def send(self,msg, dest=None):
        self._sent.append((msg,dest))

class MockChannel(object):
    implements(IChannel)
    
    dbr=_circ=None
    sid=cid=maxcount=0

    def __init__(self):
        self._C=DeferredManager()
        self._D=DeferredManager()
        self._D.callback(None)

    @property
    def whenCon(self):
        return self._C.get()
    @property
    def whenDis(self):
        return self._D.get()

    def doCon(self):
        self._D=DeferredManager()
        self._C.callback(self)

    def doFail(self):
        d, self._C = self._C, DeferredManager()
        d.callback(None)

    def doLost(self):
        self._C=DeferredManager()
        d, self._D = self._D, DeferredManager()

class TestGet(unittest.TestCase):

    timeout=2

    def setUp(self):
        self.chan=MockChannel()
        self.chan._circ=MockCircuit()
        self.chan.dbr=DBR.STRING
        self.chan.maxcount=1

    def tearDown(self):
        if hasattr(self, 'get'):
            self.get.close()
            del self.get
        import gc
        gc.collect()
        if hasattr(self, 'check'):
            # Ensure no remaining references
            self.assertTrue(self.check() is None)

    def test_noop(self):
        """Setup and tear down without running reactor.
        """

        self.get=CAGet(self.chan)
        self.check=ref(self.get)

        # circuit not connected
        self.assertEqual(len(self.chan._circ.pendingActions), 0)

        self.get.close()

        self.assertEqual(len(self.chan._circ.pendingActions), 0)

        del self.get

    def test_cancellive(self):
        """Connect but cancel after data request sent
        """

        g=self.get=CAGet(self.chan)
        self.check=ref(self.get)

        self.chan.doCon()
        self.assertEqual(len(self.chan._circ._sent), 1)
        self.assertEqual(len(self.chan._circ.pendingActions), 1)

        pkt,_=self.chan._circ._sent[0]
        self.assertEqual(len(pkt), 16)
        pkt,extra=CAmessage.unpack(pkt)

        self.assertEqual(extra, '')
        self.assertEqual(pkt.cmd, 15)
        self.assertEqual(pkt.p1, self.chan.sid)
        self.assertIn(pkt.p2, self.chan._circ.pendingActions)

        self.get.close()

        del self.get

    def test_canceldead(self):
        """Connect, lose connection, cancel
        """

        g=self.get=CAGet(self.chan)
        self.check=ref(self.get)

        self.chan.doCon()
        pkt,_=self.chan._circ._sent.pop(0)
        self.assertEqual(len(pkt), 16)
        pkt,extra=CAmessage.unpack(pkt)

        self.assertEqual(extra, '')
        self.assertEqual(pkt.cmd, 15)

        self.chan.doLost()

        self.get.close()

        del self.get
