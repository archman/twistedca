# -*- coding: utf-8 -*-

from twisted.internet import reactor

#from twisted.internet.base import DelayedCall
#DelayedCall.debug=True

from twisted.internet.defer import gatherResults, inlineCallbacks
from twisted.internet.task import deferLater
from twisted.trial import unittest
from twisted.internet.protocol import ServerFactory

from TwCA.util.config import Config
from TwCA.util.ca import CAmessage, padString, searchbody
from TwCA.util.twistedhelper import CAExpectProtocol, CAExpectDatagramProtocol
from TwCA.util.defs import CA_VERSION

from TwCA.cac.client import CAClient
from TwCA.cac.clichannel import CAClientChannel

class CAExpectFactory(ServerFactory):
    protocol=CAExpectProtocol
    tst=None
    program=None
    halt=False
    
    def buildProtocol(self, _):
        p=self.protocol(self.tst, self.program, self.halt)
        #p.debug=True
        return p


class TestChannelBasic(unittest.TestCase):

    timeout=4

    def setUp(self):
        
        self.conf=Config(Config.empty)
        
        self.cli=CAClient(self.conf, user='testuser',
                                     host='testhost')

    def tearDown(self):
        if hasattr(self, 'chan'):
            self.chan.close()
        return self.cli.close()

    def test_noop(self):

        self.chan=CAClientChannel('testpv', self.cli)


    def test_nolookup(self):
        """Connect to non-existent channel
        """

        self.chan=CAClientChannel('missingpv', self.cli)
        
        d=self.chan.whenCon
        @d.addCallback
        def onFail(conn):
            self.assertTrue(conn is None)

        d2=deferLater(reactor, 0.4, self.chan.close)

        return gatherResults([d, d2])
