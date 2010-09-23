# -*- coding: utf-8 -*-

import unittest
from copy import deepcopy
from array import array

from cas import cadata
import cas.defs as defs
from cas.convert import dbr_convert_value, dbr_convert_meta_value

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

class TestConvert(unittest.TestCase):

    def _runtest(self, dbf, val, meta, expected):
        for t, v in expected:
            conv = dbr_convert_value(dbf, t)
            r = conv(val, **meta)
            try:
                self.assertEqual(r, v)
            except AssertionError, e:
                raise AssertionError(str(e)+' for type %d'%t)
    
    def test_string(self):
        dbf=defs.DBF_STRING
        meta={'prec':2, 'strs':['1','4']}
        val=['4']
        
        fin=[(defs.DBR_STRING, ['4']),
             (defs.DBR_INT,    [4]),
             (defs.DBR_LONG,   [4]),
             (defs.DBR_CHAR,   '4'),
             (defs.DBR_FLOAT,  [4.0]),
             (defs.DBR_DOUBLE, [4.0]),
             (defs.DBR_ENUM,   [1]),
            ]

        self._runtest(dbf, val, meta, fin)

    def test_int(self):
        dbf=defs.DBF_INT
        meta={'prec':2}
        val=range(7)
        
        fin=[(defs.DBR_STRING, ['0, 1, 2, 3, 4, 5, 6']),
             (defs.DBR_INT,    val),
             (defs.DBR_LONG,   val),
             (defs.DBR_CHAR,   val),
             (defs.DBR_FLOAT,  map(float,val)),
             (defs.DBR_DOUBLE,  map(float,val)),
             (defs.DBR_ENUM,   val),
            ]

        self._runtest(dbf, val, meta, fin)

    def test_double(self):
        dbf=defs.DBF_DOUBLE
        meta={'prec':2}
        val=map(float, range(7))
        
        fin=[(defs.DBR_STRING, ['0.00, 1.00, 2.00, 3.00, 4.00, 5.00, 6.00']),
             (defs.DBR_INT,    map(int,val)),
             (defs.DBR_LONG,   map(int,val)),
             (defs.DBR_CHAR,   map(int,val)),
             (defs.DBR_FLOAT,  val),
             (defs.DBR_DOUBLE, val),
             (defs.DBR_ENUM,   map(int,val)),
            ]

    def test_enum(self):
        dbf=defs.DBF_ENUM
        meta={'prec':2, 'strs':['a','b','c']}
        val=[2]
        
        fin=[(defs.DBR_STRING, ['c']),
             (defs.DBR_INT,    [2]),
             (defs.DBR_LONG,   [2]),
             (defs.DBR_CHAR,   2),
             (defs.DBR_FLOAT,  [2.0]),
             (defs.DBR_DOUBLE, [2.0]),
             (defs.DBR_ENUM,   [2]),
            ]

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

class TestFromStringString(unittest.TestCase):
    
    def setUp(self):
        self.meta=cadata.caMeta(defs.DBF_STRING)
        self.bmeta=deepcopy(self.meta)
    
    def _check_value(self, val, meta):
        self.assertEqual(meta.dbf, defs.DBR_STRING)
        self.assertEqual(len(val), 1)
        self.assertEqual(val, ['hello world'])
    
    def test_string(self):
        val, rmeta=cadata.fromstring('hello world'+('\0'*5),
                                   defs.DBR_STRING, 1, self.meta)
        self.assertEqual(self.meta, self.bmeta)
        self._check_value(val, rmeta)

    def test_string_sts(self):
        val, rmeta=cadata.fromstring('\x12\x34\x10\x20hello world'+('\0'*9),
                                   defs.DBR_STS_STRING, 1, self.meta)
        self.assertEqual(self.meta, self.bmeta)
        self.assertEqual(rmeta.status, 0x1234)
        self.assertEqual(rmeta.severity, 0x1020)
        self._check_value(val, rmeta)

    def test_string_char(self):
        val, rmeta=cadata.fromstring('hello world'+('\0'*5),
                                   defs.DBR_CHAR, 11, self.meta)
        self.assertEqual(self.meta, self.bmeta)
        self._check_value(val, rmeta)


if __name__ == '__main__':
    #import logging
    #logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    unittest.main()
