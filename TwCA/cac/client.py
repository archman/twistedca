# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('cac.client')
from copy import copy

from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.internet.defer import Deferred, fail

from TwCA.util.config import Config

from resolver import Resolver
from circuit import CACircuitFactory

class CAClientShutdown(Exception):
    pass

class CAClient(object):
    # default client context
    default=None
    
    running=True

    def __init__(self, conf=Config.default, user=None, host=None):
        self.conf=conf
        
        self.resolv=Resolver()
        
        self.circuits=CACircuitFactory(self)
        self.closeList=set()

        if host is None:
            from socket import gethostname
            host=gethostname()
        self.host=host

        if user is None:
            from getpass import getuser
            user=getuser()
        self.user=user

        reactor.addSystemEventTrigger("before", "shutdown", self.close)

    def close(self):
        self.running=False

        for c in copy(self.closeList):
            c()

        self.resolv.close()

        self.circuits.close()

    def lookup(self, name):
        if not self.running:
            return fail()

        return self.resolv.lookup(name)

    def openCircuit(self, srv):
        if not self.running:
            return fail()

        return self.circuits.requestCircuit(srv)

    def dispatchtcp(self, pkt, peer, circuit):
        if pkt is None:
            return # circuit closed
        log.info('Client received from %s %s',peer,pkt)

CAClient.default=CAClient()
