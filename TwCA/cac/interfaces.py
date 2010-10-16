# -*- coding: utf-8 -*-

from zope.interface import Interface, Attribute

class IDispatch(Interface):
    """A sink for CA packets
    """

    def dispatch(pkt, endpoint, peer=None):
        """Packet receiver
        
        endpoint is TCP if peer is None
        or UDP if peer is not None
        """

class IClient(Interface):
    
    def close(self):
        """Shutdown the client context
        
        Fail all pending operations.
        _Not_ reversable
        """

    reactor = Attribute(
        "The reactor to be used by all sub-units")

    def lookup(name):
        """Request a lookup on a PV name.
        
        Returns a Deferred() which will be called with
        a value which can be passed to openCircuit() or
        None if a Name lookup is not possible.
        Name lookups only fail when the client context
        is closed.
        """

    def openCircuit(srv):
        """Request a circuit to the given CA server.
        
        Returns a Deferred() which is called with an
        instance of CAClientcircuit or None (failure).
        This request fails if the circuit can not be
        opened.
        """

class IClientcircuit(Interface):
    
    def addchan(channel):
        """Add a channel to this circuit
        """

    def dropchan(channel):
        """Remove a channel from this circuit
        """

    def send(msg, dest=None):
        """Send a message to the client
        """
