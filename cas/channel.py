# -*- coding: utf-8 -*-

import logging
from pv import CAError
from util.ca import CAmessage, padString, packCAerror

log=logging.getLogger('cas.channel')

class Channel(object):
    
    def __init__(self, sid, cid, server, circuit, pv):
        self.server, self.circuit=server, circuit
        self.pv, self.sid, self.cid=pv, sid, cid

        self._chan={15:self.readnotify}

        # inform circuit
        self.circuit.closeList.add(self.close)

        # inform PV
        self.pv.connect(self)
        log.debug('Create Channel')

    def close(self):
        log.debug('Destroy Channel')
        self.pv.disconnect(self)

        self.circuit.closeList.remove(self.close)
        self.circuit.dropchan(self)

    def readnotify(self, pkt, peer, circuit):
        log.debug('Read from test')
        try:
            data=self.pv.get(self, pkt.dtype, pkt.count)
            data=padString(data)
            
            pkt.cmd=15
            pkt.size=len(data)
            pkt.body=data
            self.circuit.send(pkt.pack())
        except CAError,e:
            log.exception('Read failed')
            

    def dispatch(self, pkt, peer, circuit):
        
        hdl=self._chan.get(pkt.cmd, self.server.dispatchtcp)
        
        hdl(pkt, peer, self)


