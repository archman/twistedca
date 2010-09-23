# -*- coding: utf-8 -*-

import unittest

from array import array
from cas import cadata
import cas.defs as defs

class TestSerialize(unittest.TestCase):
    
    def test_native(self):
        data=[(defs.DBR_STRING, ['hello world'],
               'hello world'+('\0'*5)),
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

class TestToString(unittest.TestCase):
    
    def test_string(self):
        meta = cadata.caMeta(defs.DBF_STRING)
        val=['hello world']
        meta.status=0x1234
        meta.severity=0x1020
        meta.stamp=1284327459.1030619

        one, count=cadata.tostring(val, meta, defs.DBR_STRING, 1)
        self.assertEqual(meta.dbf, defs.DBF_STRING)
        self.assertEqual(count, 1)
        self.assertEqual(one, 'hello world'+('\0'*5))

        one, count=cadata.tostring(val, meta, defs.DBR_STS_STRING, 1)
        self.assertEqual(meta.dbf, defs.DBF_STRING)
        self.assertEqual(count, 1)
        self.assertEqual(len(one), 24)
        self.assertEqual(one, '\x12\x34\x10\x20hello world'+('\0'*9))

        one, count=cadata.tostring(val, meta, defs.DBR_CHAR, 16)
        self.assertEqual(meta.dbf, defs.DBF_STRING)
        self.assertEqual(count, 11)
        self.assertEqual(len(one), 16)
        self.assertEqual(one, 'hello world'+('\0'*5))

    def test_int(self):
        meta = cadata.caMeta(defs.DBF_INT)
        val=[5]
        meta.status=0x1234
        meta.severity=0x1020
        meta.stamp=1284327459.1030619

        one, count=cadata.tostring(val, meta, defs.DBR_INT, 1)
        self.assertEqual(count, 1)
        self.assertEqual(one, '\x00\x05'+('\0'*6))

        one, count=cadata.tostring(val, meta, defs.DBR_STRING, 1)
        self.assertEqual(count, 1)
        self.assertEqual(one, '5'+('\0'*7))

    def test_intarray(self):
        meta = cadata.caMeta(defs.DBF_INT)
        val=range(5,15)
        meta.status=0x1234
        meta.severity=0x1020
        meta.stamp=1284327459.1030619

        one, count=cadata.tostring(val, meta, defs.DBR_INT, 20)
        self.assertEqual(count, 10)
        self.assertEqual(one,
            reduce(str.__add__,[chr(0)+chr(n) for n in range(5,15)],'')
            +('\0'*4))

        one, count=cadata.tostring(val, meta, defs.DBR_STRING, 1)
        self.assertEqual(count, 1)
        self.assertEqual(one, '5, 6, 7, 8, 9, 10, 11, 12, 13, 14'+('\0'*7))

class TestFromString(unittest.TestCase):
    
    def test_string(self):
        meta = cadata.caMeta(defs.DBF_STRING)
        val, rmeta=cadata.fromstring('hello world'+('\0'*5),
                                   defs.DBR_STRING, 1, meta)
        self.assertEqual(meta.dbf, defs.DBR_STRING)
        self.assertEqual(len(val), 1)
        self.assertEqual(val, ['hello world'])

    def test_string_sts(self):
        meta = cadata.caMeta(defs.DBF_STRING)
        val, rmeta=cadata.fromstring('\x12\x34\x10\x20hello world'+('\0'*9),
                                   defs.DBR_STS_STRING, 1, meta)
        self.assertEqual(meta.dbf, defs.DBF_STRING)
        self.assertEqual(rmeta.dbf, defs.DBF_STRING)
        self.assertEqual(rmeta.status, 0x1234)
        self.assertEqual(rmeta.severity, 0x1020)
        self.assertEqual(len(val), 1)
        self.assertEqual(val, ['hello world'])

    def test_string_char(self):
        meta = cadata.caMeta(defs.DBF_STRING)
        self.assertEqual(meta.dbf, defs.DBF_STRING)

        val, rmeta=cadata.fromstring('hello world'+('\0'*5),
                                   defs.DBR_CHAR, 11, meta)
        self.assertEqual(meta.dbf, defs.DBF_STRING)
        self.assertEqual(rmeta.dbf, defs.DBF_CHAR)

        self.assertEqual(len(val), 1)
        self.assertEqual(val, ['hello world'])

if __name__ == '__main__':
    #import logging
    #logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    unittest.main()
