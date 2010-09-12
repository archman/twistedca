# -*- coding: utf-8 -*-

import unittest

from array import array
from cas import cadata
import cas.defs as defs

class TestSerialize(unittest.TestCase):
    
    def test_native(self):
        data=[(defs.DBR_STRING, ['hello world'],
               'hello world'+('\0'*29)),
              (defs.DBR_INT, array('H',[0x1234]), '\x12\x34'),
             ]

        for dbr, inp, out in data:
            conv=cadata.dbr_value(dbr)

            one=conv.pack(inp)
            
            self.assertEqual(one, out)
            
            two=conv.unpack(out)
            
            self.assertEqual(two, inp)

    def test_sts(self):
        data=[(defs.DBR_INT, (0x1234,0x1020),
               '\x12\x34\x10\x20'),
              (defs.DBR_CHAR, (0x1234,0x1020),
               '\x12\x34\x10\x20\x00'),
              (defs.DBR_DOUBLE, (0x1234,0x1020),
               '\x12\x34\x10\x20\x00\x00\x00\x00'),
             ]

        for dbr, inp, out in data:
            conv=cadata.dbr_sts(dbr)
            
            one=conv.pack(*inp)
            
            self.assertEqual(one, out)
            
            two=conv.unpack(out)
            
            self.assertEqual(two, inp)

    #TODO: test time

    #TODO: test GR

    #TODO: test ctrl

class TestcaValue(unittest.TestCase):
    
    def test_string(self):
        val = cadata.caValue(defs.DBF_STRING)
        val.value=['hello world']
        val.status=0x1234
        val.severity=0x1020
        val.stamp=1284327459.1030619

        one, count=val.tostring(defs.DBR_STRING, 1)
        self.assertEqual(count, 1)
        self.assertEqual(one, 'hello world'+('\0'*29))

if __name__ == '__main__':
    #import logging
    #logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    unittest.main()
