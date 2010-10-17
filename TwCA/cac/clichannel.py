# -*- coding: utf-8 -*-

import logging
log=logging.getLogger('cac.clichannel')

from zope.interface import implements

from twisted.internet import reactor
from twisted.internet.defer import Deferred, succeed, inlineCallbacks
from TwCA.util.idman import DeferredManager, CBManager

from interfaces import IClientcircuit, IDispatch
from client import CAClient

class CAClientChannel(object):
    """Persistent Client Channel
    
    Handles lookups and (re)connection.
    """
    implements(IClientcircuit, IDispatch)

    S_init='Disconnected'
    S_lookup='PV lookup'
    S_waitcirc='Waiting for circuit'
    S_attach='Creating channel'
    S_connect='Connected'

    reconnectDelay=0.1
    
    def __init__(self, name, context):
        """Create a new channel to the named PV.
        
        Note: This will _always_ start a new channel even
        if one already exists.
        """
        self.name, self._ctxt=name, context

        self._connected=False # True, False, or None (shutdown)

        self._status=CBManager() # connection status callback

        self.__eventCon=DeferredManager()
        self.__eventDis=DeferredManager()
        self.__eventDis.callback(self) # initially disconnected

        # used to store a deferred during the attach phase
        self._d=None
        
        self.__T=None # reconnect delay timer

        self._chan={18:self._channelOk,
                    22:self._rights,
                    26:self._channelFail,
                    27:self._disconn,
                   }

        self._ctxt.closeList.add(self.close) #TODO: remove

        self._reset()

    @property
    def whenCon(self):
        return self.__eventCon.get()

    @property
    def whenDis(self):
        return self.__eventDis.get()

    def close(self):
        """Close the channel.

        This will fail any pending actions.
        Once called channel can not be reused.
        """
        if self._connected is None:
            # shutdown already happened
            return

        self._reset()

        if self.__T is not None:
            assert self.__T.active(), 'Timer already expired/cancelled'
            self.__T.cancel()
            self.__T=None

        if self._connected:
            self.__eventDis.callback(self)
        else:
            self.__eventCon.callback(None)
        self._connected=None
        
        # post condition
        # Both __eventDis and __eventCon are fired
        # further connection attempts fail immediately

    def _reset(self, _=None):
        """Reset to disconnected state
        
        Safe to call in all states
        """
        if self._connected is None:
            # shutdown already happened
            return

        log.debug('Channel %s reset',self.name)
        
        if self._connected is True:
            # _d is cleared before _connected is True
            assert self._d is None
            self._status(self, False)

        elif self._d:
            d, self._d = self._d, None
            d.callback(None)

        self.cid=self.sid=self.dbr=None
        self._circ=None
        self.maxcount=self.rights=0
        self.state=self.S_init

        if self._connected:
            self._connected=False
            self.__eventCon=DeferredManager()
            d, self._eventDis = self.__eventDis, None
            d.callback(self)

        elif self.__T is None:
            self.__T=reactor.callLater(self.reconnectDelay,
                                       self._connect)

    @property
    def connected(self):
        """Test if the channel is currently connected
        """
        return self._connected

    @property
    def running(self):
        """Test if the channel has been shut down
        """
        return self._connected is not None

    @inlineCallbacks
    def _connect(self):
        """Start channel connection sequence

        lookup -> open circuit -> attach channel -> connected

        only safe to call from _reset()
        """
        assert self._connected is False and self.state is self.S_init

        # prevent error when cancelling
        # _connect is invoked when __T expires
        self.__T=None

        log.debug('Channel %s connecting...',self.name)

        self.state=self.S_lookup

        srv=yield self._ctxt.lookup(self.name)
        if srv is None:
            # lookups only fail when the client is shutting down
            return

        self.state=self.S_waitcirc

        log.debug('Found %s on %s',self.name,srv)
            
        circ=yield self._ctxt.openCircuit(srv)
        if circ is None:
            # couldn't connect to server
            self._reset()
            return

        self.state=self.S_attach

        log.debug('Attaching %s to %s',self.name,circ)

        circ.addchan(self)
        self._circ=circ

        self._d=Deferred()
        
        conn=yield self._d

        assert self._d is None, '_d must be None before callback'

        if conn is None:
            # Server died while we were attaching
            self._reset()
            return

        elif conn is False:
            # channel not present on server
            log.info('channel %s rejected by server', self.name)
            self._reset()
            return

        log.debug('Channel %s Open',self.name)

        self.state=self.S_connect

        self.__eventDis=DeferredManager()
        self.__eventCon.callback(self)
        self._connected=True

        self._status(self, True)
        
        d=circ.transport.connector.whenDis
        d.addCallback(self._circuitLost)

    def _circuitLost(self,_):
        log.debug('Channel %s lost circuit',self.name)
        if self._d:
            d, self._d = self._d, None
            d.callback(None)
            self._circ=None
            # _connect() will reset

        else:
            self._reset()

    def _disconn(self, pkt, peer, circuit):
        """Server has stopped providing the channel
        """
        log.warning('Server has disconnected %s',self.name)
        self._reset()

    def _channelOk(self, pkt, peer, circuit):
        self.dbr, self.maxcount=pkt.dtype, pkt.count
        self.sid=pkt.p2

        self._checkReady()

    def _channelFail(self, pkt, peer, circuit):
        log.info('Server %s rejects channel %s',peer,self.name)
        
        self._reset()
        if self._d:
            d, self._d = self._d, None
            d.callback(False)

    def _rights(self, pkt, peer, circuit):
        self.rights=pkt.p2
        
        self._checkReady()

    def _checkReady(self):
        """Sometimes the access rights message preceeds the
        ack of channel creation...
        """
        if self.sid is None or self.rights is None:
            return
        if self._d:
            d, self._d = self._d, None
            d.callback(True)

    def dispatch(self, pkt, peer, circuit):
        assert circuit is self._circ
        
        hdl=self._chan.get(pkt.cmd, self._ctxt.dispatchtcp)
        
        if hdl:
            hdl(pkt, peer, self)
        else:
            log.debug('Channel %s received unknown %s',self.name,pkt)

    def __str__(self):
        return 'Channel %(name)s %(state)s %(cid)s:%(sid)s %(dbr)s %(maxcount)s'%self.__dict__
