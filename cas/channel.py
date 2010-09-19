# -*- coding: utf-8 -*-

import logging
from pv import CAError
from util.ca import CAmessage, padString, packCAerror, monitormask
from error import ECA_NORMAL, ECA_BADCHID
import error

log=logging.getLogger('cas.channel')

class Channel(object):
    
    def __init__(self, sid, cid, server, circuit, pv):
        self.server, self.circuit=server, circuit
        self.pv, self.sid, self.cid=pv, sid, cid

        self._chan={1 :self.monitoradd,
                    2 :self.monitordel,
                    4 :self.write,
                    15:self.readnotify,
                    19:self.write}

        self.monitors={}

        # inform circuit
        self.circuit.closeList.add(self.close)

        # inform PV
        self.pv.connect(self)
        log.debug('Create %s',self)

    def close(self, connected=False):
        log.debug('Destroy %s',self)
        self.pv.disconnect(self)
        
        if connected:
            pkt = CAmessage(cmd=27, p1=self.cid)
            self.circuit.send(pkt.pack())

        self.circuit.closeList.remove(self.close)
        self.circuit.dropchan(self)

    def post(self, mask):
        for c in self.monitors.values():
            c.post(mask)

    def readnotify(self, pkt, peer, circuit):
        log.debug('Read %s',self.pv.name)
        try:
            data, count=self.pv.get(self, pkt.dtype, pkt.count)
            
            pkt.cmd=15
            pkt.size=len(data)
            pkt.count=count
            pkt.p1=error.ECA_NORMAL
            pkt.body=data
        except CAError,e:
            log.exception('Read failed: '+e.msg)
            pkt.size=0
            pkt.count=0
            pkt.p1=e.code
            pkt.body=''
            

        raw=pkt.pack()
        print 'send',repr(raw)
        self.circuit.send(raw)

    def write(self, pkt, peer, circuit):
        log.debug('Write %s',self.pv.name)
        try:
            self.pv.set(self, pkt.body, pkt.dtype, pkt.count)
            
            if pkt.cmd==19:
                pkt.size=0
                pkt.p1=error.ECA_NORMAL
                pkt.body=''

        except CAError, e:
            log.exception('Write failed')
            if pkt.cmd==19:
                pkt.size=0
                pkt.p1=e.code
                pkt.body=''

        self.circuit.send(pkt.pack())

    def monitoradd(self, pkt, peer, circuit):

        if pkt.p2 in self.monitors:
            raise CAError('Attempt to use already existing monitor',ECA_BADCHID)

        mask, = monitormask.unpack(pkt.body)

        mon=monitor(self, pkt.p2, pkt.dtype, pkt.count, mask)
        try:
            log.debug('Add %s',mon)
            mon.post(mask)
        except CAError,e:
            log.exception('failed to create monitor')
            return

        self.monitors[mon.ioid]=mon

    def monitordel(self, pkt, peer, circuit):
        if pkt.p2 not in self.monitors:
            raise CAError('Attempt to cancel non-existant monitor',ECA_BADCHID)
        
        mon = self.monitors.pop(pkt.p2)
        log.debug('Del %s',mon)
        
        pkt = CAmessage(cmd=1, dtype=mon.dbr, p1=self.circuit.cid, p2=mon.ioid)
        self.circuit.send(pkt.pack())

    def dispatch(self, pkt, peer, circuit):
        
        hdl=self._chan.get(pkt.cmd, self.server.dispatchtcp)
        
        hdl(pkt, peer, self)

    def __str__(self):
        return 'Channel %(sid)s to %(peer)s for %(pv)s' % \
            {'sid':self.sid, 'peer':self.circuit.peer, 'pv':self.pv.name}

class monitor(object):
    
    def __init__(self, channel, ioid, dbr, count, mask):
        self.channel, self.ioid = channel, ioid
        self.dbr, self.count, self.mask = dbr, count, mask
        
    def post(self, mask):
        if (self.mask&mask)==0:
            return
        try:
            data, count = self.channel.pv.get(self.channel,
                                              self.dbr,
                                              self.count)

            pkt = CAmessage(cmd=1, size=len(data), dtype=self.dbr,
                            count=count, p1=ECA_NORMAL, p2=self.ioid,
                            body=data)
            log.debug('post to %s',self.channel.circuit.peer)
        except CAError,e:
            log.exception('Post failed')
            pkt = CAmessage(cmd=1, size=0, dtype=self.dbr,
                            count=0, p1=e.code, p2=self.ioid)

        self.channel.circuit.send(pkt.pack())

    def __str__(self):
        return 'Monitor on %s for %d'%(str(self.channel),self.mask)
