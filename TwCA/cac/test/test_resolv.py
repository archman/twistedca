# -*- coding: utf-8 -*-

from twisted.internet import reactor

#from twisted.internet.base import DelayedCall
#DelayedCall.debug=True

from twisted.internet.defer import gatherResults
from twisted.trial import unittest

from TwCA.util.config import Config
from TwCA.util.ca import CAmessage, padString, searchbody
from TwCA.util.twistedhelper import CAExpectProtocol, CAExpectDatagramProtocol
from TwCA.util.defs import CA_VERSION

from TwCA.cac.resolver import Resolver

class StubClient:
    user='hello'
    host='world'
    reactor=reactor
    def dispatch(self, pkt, _):
        self.fail('Unexpected packet %s',pkt)

class TestResolver(unittest.TestCase):
    
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

    def tearDown(self):
        d1=self.up.stopListening()
        d2=self.resolv.close()
        return gatherResults([d1,d2])
