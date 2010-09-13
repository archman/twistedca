#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncore, logging
#from util.timer import Queue, Timer
from cas.pv import BasicPV
from cas.server import Server
from cas.defs import DBF_STRING, DBF_LONG

def main():
    
    test=BasicPV('test', dtype=DBF_STRING, value=['hello world'])
    test2=BasicPV('test2', dtype=DBF_LONG, value=[42])
    test3=BasicPV('test3', dtype=DBF_LONG, value=range(10))
    
    p = Server(pvs=[test,test2,test3])
    
    asyncore.loop()

if __name__=='__main__':
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    main()
