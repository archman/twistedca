#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, sys
log=logging.getLogger('TwCA.caput')

from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning
from twisted.internet.defer import DeferredList

from TwCA import __version__ as TwCAVersion
from TwCA.cac.client import CAClient
from TwCA.cac.clichannel import CAClientChannel
from TwCA.cac.get import CAGet
from TwCA.cac.set import CASet
from TwCA.util.defs import *
from TwCA.util.error import ECA_NORMAL

from optparse import OptionParser

p=OptionParser(version=TwCAVersion,
usage="%prog [options] pvname value ...",
description="""
Channel Access writer
""")

p.add_option('-v', '--verbose', default=0,
             help='Make more noise', action='count')
p.add_option('-q', '--quiet', default=0,
             help='Make less noise', action='count')

p.add_option('-w', '--tmo', type="float", default=5.0,
             help='Get Timeout')

p.add_option('-x', '--nowait', action="store_true",
             help="Don't wait for completion")

p.add_option('-d', '--dbr', type="string", default=None,
             help='Request specific datatype')
p.add_option('-S', '--char', action="store_true",
             help='Send string as char array')
p.add_option('-a', '--array', action="store_true",
             help='Send array (treats whitespace as separator)')

opt, args=p.parse_args()

if opt.dbr is not None and opt.char:
    p.error('--dbr N and --char are incompatible')

if len(args)<2:
    p.error('missing pvname or value')

pv=args.pop(0)

LVL={-2:logging.CRITICAL, -1:logging.ERROR, 0:logging.WARNING,
      1:logging.INFO,      2:logging.DEBUG}
verb=opt.verbose-opt.quiet
verb=max(-2, min(verb, 2))

logging.basicConfig(format='%(message)s',level=LVL[verb])

dbr=DBR.STRING

def timeout():
    log.fatal('Timeout!')
    try:
        reactor.stop()
    except ReactorNotRunning:
        pass

if opt.tmo >=0.00001:
    reactor.callLater(opt.tmo, timeout)

client=CAClient()

chan=CAClientChannel(pv, client)



# request native type and convert to string locally
g=CAGet(chan, dbf_conv=DBF.STRING)
d=g.data

@d.addCallback
def startSet((data,_)):
    print 'Before:',
    for d in data:
        print d,
    print
    
    s=CASet(chan, args, dbf=dbr, wait=not opt.nowait)

    return s.complete

@d.addCallback
def getUpdated(sts):
    if sts!=ECA_NORMAL:
        print 'Error:', sts

    d2=CAGet(chan, dbf_conv=DBF.STRING)
    return d2.data

@d.addCallback
def finalValue((data,_)):
    print 'After:',
    for d in data:
        print d,
    print

@d.addErrback
def oops(fail):
    print fail
    return fail

@d.addBoth
def stop(x):
    try:
        reactor.stop()
    except ReactorNotRunning:
        pass
    return x


reactor.run()
