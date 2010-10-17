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

class IConnectNotify(Interface):
    """Object has a connected and disconnecte states
    and uses
    """
    
    whenCon=Attribute("""
       A Deferred which fires when the object
       becomes connected.
       
       The deferred will be called with a reference to
       the object (ie self) or None for a failed
       connection attempt.
       
       Shared objects may implement this as a property
       and return a different deferred for each read.
       """)
    
    whenDis=Attribute("""
       A Deferred which fires when the object
       becomes disconnected.
       
       The deferred will be called with a reference to
       the object (ie self).
       
       Shared objects may implement this as a property
       and return a different deferred for each read.
       """)
