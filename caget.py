#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, sys
log=logging.getLogger('caget')

from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning
from twisted.internet.defer import DeferredList

from TwCA import __version__ as TwCAVersion
from TwCA.cac.clichannel import CAClientChannel
from TwCA.cac.get import CAGet
from TwCA.util.defs import *
from TwCA.util.cadata import printMeta

from optparse import OptionParser

p=OptionParser(version=TwCAVersion,
usage="%prog [options] pvname value ...",
description="""
Channel Access read
""")

p.add_option('-v', '--verbose', default=0,
             help='Make more noise', action='count')
p.add_option('-q', '--quiet', default=0,
             help='Make less noise', action='count')

p.add_option('-w', '--tmo', type="float", default=5.0,
             help='Get Timeout')

p.add_option('-a', '--time', action="store_true",
             help='Request time meta-data')
p.add_option('-d', '--dbr', type="string", default=None,
             help='Request specific datatype')
p.add_option('-n', '--noenum', action="store_true",
             help='Print enum as string')
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
meta_req=META.PLAIN
dbf_dis=None
count=opt.count

if opt.char and opt.str:
    p.error("--char and --str are incompatible")

if opt.dbr is not None and opt.str:
    p.error('--dbr N and --str are incompatible')

if opt.dbr is not None and opt.time:
    p.error('--dbr N and --time are incompatible')

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

if opt.time:
    meta_req=META.TIME

dcnt='Native' if count is None else count
log.info('Requesting %s %s (%s) as %s',
         dbf_req, meta_req, count, dbf_dis)

def channelCB(chan, status):
    log.info(chan)

def data(data, pv, cls):
    value,meta=data
    print pv,':',
    for v in value:
        print v,
    print printMeta(meta,cls),
    return data

def nodata(_, pv):
    print pv,': *** No Data ***'

def stop(x):
    try:
        reactor.stop()
    except ReactorNotRunning:
        pass
    return x

def timeout():
    log.fatal('Timeout!')
    try:
        reactor.stop()
    except ReactorNotRunning:
        pass

if opt.tmo >=0.00001:
    reactor.callLater(opt.tmo, timeout)

gets=[]

for pv in pvs:
    chan=CAClientChannel(pv, channelCB)

    g=CAGet(chan, dbf_req, count, meta=meta_req,
            dbf_conv=dbf_dis)
    g.data.addCallback(data, pv, meta_req)
    g.data.addErrback(nodata, pv)
    gets.append(g.data)

done=DeferredList(gets)
done.addBoth(stop)

reactor.run()
