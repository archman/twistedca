# -*- coding: utf-8 -*-

import unittest
from copy import deepcopy
from array import array

from TwCA.util import cadata
import TwCA.util.defs as defs
from TwCA.util.convert import dbr_convert_value, dbr_convert_meta_value

class TestSerialize(unittest.TestCase):
    
    def test_native(self):
        data=[(defs.DBR.STRING, ['hello world'],
               'hello world'+('\0'*5)),
              (defs.DBR.INT, array('H',[0x1234]), '\x12\x34'),
             ]

        for dbr, inp, out in data:
            conv=cadata.dbr_value(dbr)

            one=conv.pack(inp)
            
            self.assertEqual(one, out)
            
            two=conv.unpack(out)
            
            self.assertEqual(two, inp)

    def test_stringarray(self):
        # strings padded to 40 bytes
        raw=reduce(str.__add__,[str(i)+39*'\0' for i in range(1,10)],'')
        # the list string is only padded to the 8 byte boundary
        raw+='10'+6*'\0'

        conv=cadata.dbr_value(defs.DBR.STRING)
        
        x=conv.unpack(raw)

        self.assertEqual(len(x), 10)
        self.assertEqual(x, ['1','2','3','4','5','6','7','8','9','10'])

        y=conv.pack(x)

        self.assertEqual(len(y), len(raw))
        self.assertEqual(y, raw)

        

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
        dbf=defs.DBF.STRING
        meta={'prec':2, 'strs':['1','4']}
        val=['4']
        
        fin=[(defs.DBR.STRING, ['4']),
             (defs.DBR.INT,    [4]),
             (defs.DBR.LONG,   [4]),
             (defs.DBR.CHAR,   '4'),
             (defs.DBR.FLOAT,  [4.0]),
             (defs.DBR.DOUBLE, [4.0]),
             (defs.DBR.ENUM,   [1]),
            ]

        self._runtest(dbf, val, meta, fin)

    def test_int(self):
        dbf=defs.DBF.INT
        meta={'prec':2}
        val=range(7)
        
        fin=[(defs.DBR.STRING, ['0, 1, 2, 3, 4, 5, 6']),
             (defs.DBR.INT,    val),
             (defs.DBR.LONG,   val),
             (defs.DBR.CHAR,   val),
             (defs.DBR.FLOAT,  map(float,val)),
             (defs.DBR.DOUBLE,  map(float,val)),
             (defs.DBR.ENUM,   val),
            ]

        self._runtest(dbf, val, meta, fin)

    def test_double(self):
        dbf=defs.DBF.DOUBLE
        meta={'prec':2}
        val=map(float, range(7))
        
        fin=[(defs.DBR.STRING, ['0.00, 1.00, 2.00, 3.00, 4.00, 5.00, 6.00']),
             (defs.DBR.INT,    map(int,val)),
             (defs.DBR.LONG,   map(int,val)),
             (defs.DBR.CHAR,   map(int,val)),
             (defs.DBR.FLOAT,  val),
             (defs.DBR.DOUBLE, val),
             (defs.DBR.ENUM,   map(int,val)),
            ]

    def test_enum(self):
        dbf=defs.DBF.ENUM
        meta={'prec':2, 'strs':['a','b','c']}
        val=[2]
        
        fin=[(defs.DBR.STRING, ['c']),
             (defs.DBR.INT,    [2]),
             (defs.DBR.LONG,   [2]),
             (defs.DBR.CHAR,   2),
             (defs.DBR.FLOAT,  [2.0]),
             (defs.DBR.DOUBLE, [2.0]),
             (defs.DBR.ENUM,   [2]),
            ]

class TestToString(unittest.TestCase):
    
    def test_string(self):
        meta = cadata.caMeta(defs.DBF.STRING)
        val=['hello world']
        meta.status=0x1234
        meta.severity=0x1020
        meta.stamp=1284327459.1030619

        one, count=cadata.tostring(val, meta, defs.DBR.STRING, 1)
        self.assertEqual(meta.dbf, defs.DBF.STRING)
        self.assertEqual(count, 1)
        self.assertEqual(one, 'hello world'+('\0'*5))

        one, count=cadata.tostring(val, meta, defs.DBR.STS_STRING, 1)
        self.assertEqual(meta.dbf, defs.DBF.STRING)
        self.assertEqual(count, 1)
        self.assertEqual(len(one), 24)
        self.assertEqual(one, '\x12\x34\x10\x20hello world'+('\0'*9))

        one, count=cadata.tostring(val, meta, defs.DBR.CHAR, 16)
        self.assertEqual(meta.dbf, defs.DBF.STRING)
        self.assertEqual(count, 11)
        self.assertEqual(len(one), 16)
        self.assertEqual(one, 'hello world'+('\0'*5))

    def test_int(self):
        meta = cadata.caMeta(defs.DBF.INT)
        val=[5]
        meta.status=0x1234
        meta.severity=0x1020
        meta.stamp=1284327459.1030619

        one, count=cadata.tostring(val, meta, defs.DBR.INT, 1)
        self.assertEqual(count, 1)
        self.assertEqual(one, '\x00\x05'+('\0'*6))

        one, count=cadata.tostring(val, meta, defs.DBR.STRING, 1)
        self.assertEqual(count, 1)
        self.assertEqual(one, '5'+('\0'*7))

    def test_intarray(self):
        meta = cadata.caMeta(defs.DBF.INT)
        val=range(5,15)
        meta.status=0x1234
        meta.severity=0x1020
        meta.stamp=1284327459.1030619

        one, count=cadata.tostring(val, meta, defs.DBR.INT, 20)
        self.assertEqual(count, 10)
        self.assertEqual(one,
            reduce(str.__add__,[chr(0)+chr(n) for n in range(5,15)],'')
            +('\0'*4))

        one, count=cadata.tostring(val, meta, defs.DBR.STRING, 1)
        self.assertEqual(count, 1)
        self.assertEqual(one, '5, 6, 7, 8, 9, 10, 11, 12, 13, 14'+('\0'*7))

class TestFromStringString(unittest.TestCase):
    
    def setUp(self):
        self.meta=cadata.caMeta(defs.DBF.STRING)
        self.bmeta=deepcopy(self.meta)
    
    def _check_value(self, val, meta):
        self.assertEqual(meta.dbf, defs.DBR.STRING)
        self.assertEqual(len(val), 1)
        self.assertEqual(val, ['hello world'])
    
    def test_string(self):
        val, rmeta=cadata.fromstring('hello world'+('\0'*5),
                                   defs.DBR.STRING, 1, self.meta)
        self.assertEqual(self.meta, self.bmeta)
        self._check_value(val, rmeta)

    def test_string_sts(self):
        val, rmeta=cadata.fromstring('\x00\x10\x00\x03hello world'+('\0'*9),
                                   defs.DBR.STS_STRING, 1, self.meta)
        self.assertEqual(self.meta, self.bmeta)
        self.assertEqual(rmeta.status, defs.STATUS.BAD_SUB)
        self.assertEqual(rmeta.severity, defs.SEVERITY.INVALID)
        self._check_value(val, rmeta)

    def test_string_char(self):
        val, rmeta=cadata.fromstring('hello world'+('\0'*5),
                                   defs.DBR.CHAR, 11, self.meta)
        self.assertEqual(self.meta, self.bmeta)
        self._check_value(val, rmeta)

class TestMetaProxy(unittest.TestCase):
    def test_cow(self):
        m=cadata.caMeta(defs.DBF.INT)
        p=cadata.caMetaProxy(m)
        
        m.stamp=5.1
        self.assertEqual(p.stamp, 5.1)
        p.stamp=4.9
        self.assertEqual(m.stamp, 5.1)
        self.assertEqual(p.stamp, 4.9)

    def test_ro(self):
        m=cadata.caMeta(defs.DBF.INT)
        p=cadata.caMetaProxy(m, ro=True)
        
        m.stamp=5.1
        self.assertEqual(p.stamp, 5.1)
        def x():
            p.stamp=4.9
        self.assertRaises(TypeError, x)

if __name__ == '__main__':
    #import logging
    #logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    unittest.main()
