# -*- coding: utf-8 -*-

from zope.interface import Interface, Attribute

from twisted.internet.interfaces import IProtocol

from TwCA.util.interfaces import IDispatch, IConnectNotify

class IClient(IDispatch):
    
    def close():
        """Shutdown the client context
        
        Fail all pending operations.
        _Not_ reversable
        """

    reactor = Attribute(
        "The reactor to be used by all sub-units")

    user = Attribute(
        "Username given to servers")

    host = Attribute(
        "Hostname given to servers")

    onClose = Attribute(
        "A Deferred() triggered when the client context is closed")

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

class IChannel(IDispatch, IConnectNotify):

    name=Attribute("PV name")
    dbr=Attribute("Native type")
    maxcount=Attribute("Max element count")
    sid=Attribute("Server's resource ID#")
    cid=Attribute("Client's resource ID#")

    _circ=Attribute("An object implementing IClientcircuit")

class IClientcircuit(IProtocol):

    pendingActions=Attribute("""An IDManager which maps
            action ID# to object where the objects implement
            IDispatch
            """)

    subscriptions=Attribute("""An IDManager which maps subscription
            ID# to objects which implements IDispatch
            """)

    version=Attribute("Negotiated protocol version")

    def addchan(channel):
        """Add a channel to this circuit
        """

    def dropchan(channel):
        """Remove a channel from this circuit
        """

    def send(msg, dest=None):
        """Send a message to the client
        """
