# -*- coding: utf-8 -*-

from zope.interface import Interface, Attribute

from TwCA.util.interfaces import IDispatch

class ICAServer(IDispatch):
    
    
    def Lookup(name):
        """Called in responce to name search requests.
        
        Can return either True/False, or a tuple of (ip, port).
        The ip returned must be a 32-bit integer (host order).
        """

    def GetPV(self,name):
        """Called when a client trys to create a channel
        
        Return a PV instance or None.
        """
    circuits = Attribute("""
        Set of all active TCP circuits owned by this server
        """)
