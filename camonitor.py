#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, sys
log=logging.getLogger('camonitor')
from time import strftime, localtime

from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning
from twisted.internet.defer import DeferredList

from TwCA import __version__ as TwCAVersion
from TwCA.cac.client import CAClientShutdown
from TwCA.cac.clichannel import CAClientChannel
from TwCA.cac.monitor import CAMonitor
from TwCA.util.cadata import printMeta
from TwCA.util.defs import *
from TwCA.util.error import ECA_NORMAL

from optparse import OptionParser

p=OptionParser(version=TwCAVersion,
usage="%prog [options] pvnames ...",
description="""
Channel Access monitor
""")

p.add_option('-v', '--verbose', default=0,
             help='Make more noise', action='count')
p.add_option('-q', '--quiet', default=0,
             help='Make less noise', action='count')

p.add_option('-w', '--tmo', type="float", default=0.0,
             help='Stop after (default inf.)')

p.add_option('-d', '--dbr', type="string", default=None,
             help='Request specific datatype')
p.add_option('-S', '--char', action="store_true",
             help='Treat char array as string')
p.add_option('-s', '--str', action="store_true",
             help='Request as string (server does conversion)')

p.add_option('-#', '--count', type="long", default=None,
             help='Request number of elements')

opt, pvs=p.parse_args()

LVL={-2:logging.CRITICAL, -1:logging.ERROR, 0:logging.WARNING,
      1:logging.INFO,      2:logging.DEBUG}
verb=opt.verbose-opt.quiet
verb=max(-2, min(verb, 2))

logging.basicConfig(format='%(message)s',level=LVL[verb])

dbf_req=None
meta_req=META.TIME
dbf_dis=None
count=opt.count

if opt.char and opt.str:
    p.error("--char and --str are incompatible")

if opt.dbr is not None:
    if opt.dbr.startswith('DBR_'):
        _,_,opt.dbr=opt.dbr.partition('DBR_')
    elif opt.dbr.startswith('DBF_'):
        _,_,opt.dbr=opt.dbr.partition('DBF_')

    dbr=DBR.fromString(opt.dbr)
    if dbr is None:
        p.error('Invalid dbr type %s'%dbr)
    dbf_req, meta_req=dbr_to_dbf(dbr)

if opt.str:
    dbf_req=DBF.STRING

if opt.dbr is not None and opt.str:
    p.error('--dbr N and --str are incompatible')

if opt.dbr is not None and opt.time:
    p.error('--dbr N and --time are incompatible')

dcnt='Native' if count is None else count
log.info('Requesting %s %s (%s) as %s',
         dbf_req, meta_req, count, dbf_dis)

# for display pad pv names
padlen=max(map(len,pvs))+2
def pad(pv):
    return pv+' '*(padlen-len(pv))

def printTime(stamp):
    sec=strftime("%a %b %d %Y %H:%M:%S",localtime(stamp))
    ns='%0.6f'%(stamp%1)
    ns=ns[1:] # trim leading zero
    return sec+ns

def channelCB(chan, status):
    log.info(chan)

def data(data, mask, status, pv, cls):
    print pad(pv),
    if data is None:
        print '*** Disconnected ***'
        return

    value,meta=data
    print printTime(meta.stamp),
    for v in value:
        print v,
    print

def stop():
    try:
        reactor.stop()
    except ReactorNotRunning:
        pass

if opt.tmo >=0.00001:
    reactor.callLater(opt.tmo, stop)

chans=[]

for pv in pvs:
    chan=CAClientChannel(pv, channelCB)
    
    mon=CAMonitor(chan, dbf_req, count, meta=META.TIME,
            dbf_conv=dbf_dis, mask=DBE.VALUE)

    mon.updates.add(data, pv, meta_req)

    chans.append((chan, mon))

reactor.run()
