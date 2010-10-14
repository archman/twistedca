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
    """Channel Access Client context
    
    Manages name search requests and TCP connections.
    """
    # default client context
    default=None
    
    running=True

    def __init__(self, conf=Config.default, user=None, host=None):
        """Construct a new client context
        
        Prepare a new context with the given config.
        If user and host are None then they are collected
        from the environment.
        """
        self.conf=conf
        
        self.circuits=CACircuitFactory(self)
        
        self.resolv=Resolver(self.circuits, conf)
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
        """Stop a client context.
        
        This will close all circuits and fail any pending
        actions (get, put, monitor, lookup)
        """
        if not self.running:
            return

        self.running=False

        for c in copy(self.closeList):
            c()

        self.resolv.close()

        self.circuits.close()

    def lookup(self, name):
        """Request a lookup on a PV name.
        
        Returns a Deferred() which will be called with
        a value which can be passed to openCircuit().
        Name lookups only fail when the client context
        is closed.
        """
        if not self.running:
            return fail(CAClientShutdown('Client not running'))

        return self.resolv.lookup(name)

    def openCircuit(self, srv):
        """Request a circuit to the given CA server.
        
        Returns a Deferred() which is called with an
        instance of CAClientcircuit.
        This request fails in the circuit can not be
        opened.
        """
        if not self.running:
            return fail(CAClientShutdown('Client not running'))

        return self.circuits.requestCircuit(srv)

    def dispatchtcp(self, pkt, peer, circuit):
        if pkt is None:
            return # circuit closed

        if pkt.cmd in (6,14):
            self.resolv._dataRx(pkt,(peer.host,peer.port),circuit)
        else:
            log.info('Client received unexpected from %s %s',peer,pkt)

CAClient.default=CAClient()
