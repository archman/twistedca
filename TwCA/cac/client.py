# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('TwCA.cac.client')
from copy import copy

from zope.interface import implements

from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.internet.defer import succeed

from TwCA.util.config import Config
from TwCA.util.idman import DeferredManager

from TwCA.util.interfaces import IDispatch
from interfaces import IClient

from resolver import Resolver
from circuit import CACircuitFactory

class CAClient(object):
    """Channel Access Client context
    
    Manages name search requests and TCP connections.
    """
    
    implements(IClient, IDispatch)
    
    running=True

    def __init__(self, conf=Config.default, user=None, host=None,
                 reactor=reactor):
        """Construct a new client context
        
        Prepare a new context with the given config.
        If user and host are None then they are collected
        from the environment.
        """
        self.conf, self.reactor=conf, reactor
        
        self.circuits=CACircuitFactory(self)
        
        self.resolv=Resolver(self.circuits, conf)
        self._onClose=DeferredManager()

        if host is None:
            from socket import gethostname
            host=gethostname()
        self.host=host

        if user is None:
            from getpass import getuser
            user=getuser()
        self.user=user

        reactor.addSystemEventTrigger("before", "shutdown", self.close)

    @property
    def onClose(self):
        return self._onClose.get()

    def close(self):
        """Stop a client context.
        
        This will close all circuits and fail any pending
        actions (get, put, monitor, lookup)
        
        Returns a Deferred which is called when shutdown is
        complete
        """
        if not self.running:
            return

        self.running=False

        self.onClose.callback(self)

        d=self.resolv.close()

        self.circuits.close()
        
        return d

    def lookup(self, name):
        """Request a lookup on a PV name.
        
        Returns a Deferred() which will be called with
        a value which can be passed to openCircuit() or
        None if a Name lookup is not possible.
        Name lookups only fail when the client context
        is closed.
        """
        if not self.running:
            return succeed(None)

        return self.resolv.lookup(name)

    def openCircuit(self, srv):
        """Request a circuit to the given CA server.
        
        Returns a Deferred() which is called with an
        instance of CAClientcircuit or None (failure).
        This request fails if the circuit can not be
        opened.
        """
        if not self.running:
            return succeed(None)

        return self.circuits.requestCircuit(srv)

    def dispatch(self, pkt, circuit, peer=None):

        log.info('Client received unexpected from %s %s',peer,pkt)

