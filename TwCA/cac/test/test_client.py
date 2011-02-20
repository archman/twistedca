# -*- coding: utf-8 -*-

from twisted.internet import reactor

#from twisted.internet.base import DelayedCall
#DelayedCall.debug=True

from twisted.internet.defer import gatherResults, inlineCallbacks
from twisted.trial import unittest
from twisted.internet.protocol import ServerFactory

from TwCA.util.config import Config
from TwCA.util.ca import CAmessage, padString, searchbody
from TwCA.util.twistedhelper import CAExpectProtocol, CAExpectDatagramProtocol
from TwCA.util.defs import CA_VERSION

from TwCA.cac.client import CAClient
    
class CAExpectFactory(ServerFactory):
    protocol=CAExpectProtocol
    tst=None
    program=None
    halt=False
    
    def buildProtocol(self, _):
        p=self.protocol(self.tst, self.program, self.halt)
        #p.debug=True
        return p

class TestClientBasic(unittest.TestCase):

    def test_noop(self):
        
        conf=Config(Config.empty)
        
        cli=CAClient(conf, user='testuser', host='testhost')

        return cli.close()

class TestClientCircuit(unittest.TestCase):
    
    timeout=2
    
    def tearDown(self):
        d=[]
        if hasattr(self, 'cli'):
            d.append(self.cli.close())
        if hasattr(self, 'udp'):
            d.append(self.udp.stopListening())
        if hasattr(self, 'tcp'):
            d.append(self.tcp.stopListening())
        return gatherResults(d)

    def test_opencircuit(self):
        name=padString('testpv')
        user=padString('testuser')
        host=padString('testhost')

        namelookup=CAExpectDatagramProtocol(self, [], halt=False)

        udp=self.udp=reactor.listenUDP(0, namelookup,
                                interface='127.0.0.1')

        sfact=self.sfact=CAExpectFactory()
        sfact.tst=self

        tcp=self.tcp=reactor.listenTCP(0, sfact, interface='127.0.0.1')

        udptarget='127.0.0.1', udp.getHost().port
        tcptarget='127.0.0.1', tcp.getHost().port

        # name search
        # respond after second request
        namelookup.program= \
            [('recv',CAmessage(dtype=0, count=CA_VERSION)),
             ('recv',CAmessage(cmd=6, size=len(name),
                               dtype=5, count=CA_VERSION,
                               p1=0, p2=0, body=name)),
             ('recv',CAmessage(dtype=0, count=CA_VERSION)),
             ('recv',CAmessage(cmd=6, size=len(name),
                               dtype=5, count=CA_VERSION,
                               p1=0, p2=0, body=name)),
             ('send',CAmessage(cmd=6, size=8, dtype=tcptarget[1],
                               p1=0xffffffff, p2=0,
                               body=searchbody.pack(11))),
            ]
        #namelookup.debug=True

        sfact.program= \
            [('send',CAmessage(dtype=0, count=12)),
             ('recv',CAmessage(dtype=0, count=CA_VERSION)),
             ('recv',CAmessage(cmd=20, size=len(user), body=user)),
             ('recv',CAmessage(cmd=21, size=len(host), body=host)),
             ('recv',CAmessage(cmd=100)),
            ]

        
        conf=Config(Config.empty)
        conf.addrs=[udptarget]
        
        cli=self.cli=CAClient(conf, user='testuser', host='testhost')

        
        namelookup.dest='127.0.0.1', cli.resolv._udp.getHost().port

        d=cli.lookup('testpv')
        
        @d.addCallback
        @inlineCallbacks
        def findAndConnect(srv):
            self.assertEqual(srv, tcptarget)
            
            circ=yield cli.openCircuit(srv)

            self.assertTrue(circ is not None)
            
            self.assertEqual(circ.version, 12)

        return d
