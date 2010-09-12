#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncore, logging
#from util.timer import Queue, Timer
from cas.server import Server

def main():
    
    p = Server(names=['test'])
    
    asyncore.loop()

if __name__=='__main__':
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    main()
