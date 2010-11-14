#!/usr/bin/python
# -*- coding: utf-8 -*-

from time import time
import logging, sys
log=logging.getLogger('TwCA.camonitor')

from twisted.internet import reactor

from TwCA.cac.clichannel import CAClientChannel
from TwCA.cac.monitor import CAMonitor
from TwCA.cac.client import CAClient
from TwCA.util.defs import *

from optparse import OptionParser

p=OptionParser(
usage="%prog [-v] -N #pvs -P PVprefix",
description="""
Massive client load test
""")

p.add_option('-v', '--verbose', default=0,
             help='Make more noise', action='count')
p.add_option('-q', '--quiet', default=0,
             help='Make less noise', action='count')
p.add_option('-N', '--number', type='int', default=1000,
             help='# of client PVs to connect to')
p.add_option('-P', '--prefix', default='test',
             help='PV name prefix')

opt, pvs=p.parse_args()

LVL={-2:logging.CRITICAL, -1:logging.ERROR, 0:logging.WARNING,
      1:logging.INFO,      2:logging.DEBUG}
verb=opt.verbose-opt.quiet
verb=max(-2, min(verb, 2))

logging.basicConfig(format='%(message)s',level=LVL[verb])

chans=[]

client=CAClient()

class Stats(object):
    def __init__(self, name):
        self.name=name
        self.C=None
        self.D=0
    def update(self, V, mask, sts):
        if V is None:
            self.D+=1
        elif self.C is None:
            self.C=V[0], V[1].stamp, time()
        else:
            now=time()
            val, meta = V
            old, prevIOC, prevHost = self.C
            self.C=val, meta.stamp, now
            dtIOC=meta.stamp - prevIOC
            dtHost=now - prevHost
            dv=val[0] - old[0]
            if val[0]%10==0:
                print self.name, dv, '%.3f'%(dtIOC/dtHost)
            

for N in range(1, opt.number+1):
    name='%s%d'%(opt.prefix, N)
    c=CAClientChannel(name, client)

    mon=CAMonitor(c, meta=META.TIME)

    s=Stats(name)

    mon.updates.add(s.update)

reactor.run()
