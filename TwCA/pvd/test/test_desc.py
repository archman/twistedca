# -*- coding: utf-8 -*-

#from twisted.trial import unittest
import unittest

from TwCA.pvd import desc

class TestDoc(unittest.TestCase):
    
    def test_pvd(self):
        desc._test()

class TestcreateStruct(unittest.TestCase):
 
    def compare(self, a, **kws):
        for attr, exp in kws.iteritems():
            self.assertTrue(hasattr(a, attr))
            self.assertEqual(getattr(a,attr), exp)
   
    def test_unordered(self):
        fld=desc.createStruct('test', a='int', b='double', other='string[]')
        self.checkPOD(fld)

    def test_ordered(self):
        fld=desc.createStruct('test', ('b','double'), ('a','int'),
                             ('other','string[]'))

        self.assertEqual(len(fld.children), 3)
        # swap a and b back to re-use comparison
        fld.children[0:2] = fld.children[1::-1]
        self.checkPOD(fld)
        
    def checkPOD(self, fld):
        self.compare(fld, name='test', type=desc.STRUCT)
        self.assertEqual(len(fld.children), 3)

        self.compare(fld.children[0], name='a', type=desc.INT)
        self.compare(fld.children[1], name='b', type=desc.DOUBLE)
        self.compare(fld.children[2], name='other', type=desc.STRING|desc.SCALARARRAY)

    def test_unorderedSubStruct(self):
        fld=desc.createStruct('hello', a='int', b={'c':'double', 'd':{'e':'long'}})
        self.checkStruct(fld)

    def test_orderedSubStruct(self):
        fld=desc.createStruct('hello', ('b', [
                                        ('d',[
                                            ('e','long'),
                                        ] ),
                                        ('c','double'),
                                    ]),
                            ('a','int'))
        # swap c and d back to re-use comparison
        fld.children[0].children[0:2] = fld.children[0].children[1::-1]
        # swap a and b back to re-use comparison
        fld.children[0:2] = fld.children[1::-1]
        self.checkStruct(fld)
        
    def checkStruct(self, fld):
        self.compare(fld, name='hello', type=desc.STRUCT)
        self.assertEqual(len(fld.children), 2)
        self.compare(fld.children[0], name='a', type=desc.INT)
        self.compare(fld.children[1], name='b', type=desc.STRUCT)
        self.assertEqual(len(fld.children[1].children), 2)
        self.compare(fld.children[1].children[0], name='c', type=desc.DOUBLE)
        self.compare(fld.children[1].children[1], name='d', type=desc.STRUCT)
        self.assertEqual(len(fld.children[1].children[1].children), 1)
        self.compare(fld.children[1].children[1].children[0], name='e', type=desc.LONG)

    def test_unorderedSubStructArray(self):
        fld=desc.createStruct('hello', a='int', b=[{'c':'double', 'd':[{'e':'long'}]}])
        self.checkStructArray(fld)

    def test_orderedSubStructArray(self):
        fld=desc.createStruct('hello', ('b', [[
                                        ('d',[[
                                            ('e','long'),
                                        ]] ),
                                        ('c','double'),
                                    ]]),
                            ('a','int'))
        # swap c and d back to re-use comparison
        fld.children[0].children[0:2] = fld.children[0].children[1::-1]
        # swap a and b back to re-use comparison
        fld.children[0:2] = fld.children[1::-1]
        self.checkStructArray(fld)
        
    def checkStructArray(self, fld):
        self.compare(fld, name='hello', type=desc.STRUCT)
        self.assertEqual(len(fld.children), 2)
        self.compare(fld.children[0], name='a', type=desc.INT)
        self.compare(fld.children[1], name='b', type=desc.STRUCTARRAY)
        self.assertEqual(len(fld.children[1].children), 2)
        self.compare(fld.children[1].children[0], name='c', type=desc.DOUBLE)
        self.compare(fld.children[1].children[1], name='d', type=desc.STRUCTARRAY)
        self.assertEqual(len(fld.children[1].children[1].children), 1)
        self.compare(fld.children[1].children[1].children[0], name='e', type=desc.LONG)

class TestBasic(unittest.TestCase):

    def setUp(self):
        self.ctxt=desc.FieldContext()
    
    def test_struct(self):
        for fld, raw in [
                (desc.createStruct('test1', value='int', hello='double[]'),
                 '\xfd\x00\x01\x20\x05test1' # struct test1 {
                     +'\x02' # 2 members
                         +'\x16\x05hello'
                         +'\x03\x05value'
                     ),
                (desc.createStruct('test1', ('value','int'), ('hello','double[]')),
                 '\xfd\x00\x02\x20\x05test1' # struct test1 {
                     +'\x02' # 2 members
                         +'\x03\x05value'
                         +'\x16\x05hello'
                     ),
                ]:
            id, act=self.ctxt.encode(fld)
            self.assertEqual(act, raw)

    def test_example(self):
        ts=desc.createStruct('timeStamp', ('secondsPastEpoch','long'),
                            ('nanoSeconds','int'))

        alm=desc.createStruct('alarm', ('severity','int'), ('message','string'))
        
        elm=desc.createStruct('element',
                             ('value','double'), alm, ts)
        
        fld=desc.createStruct('test1',
                             ts,
                             ('value', [[('value','double'),
                                         ('location', [('x','double'),
                                                       ('y','double')])
                                                       ]]),
                             ('factoryRPC', 'string'),
                             desc.createStruct('arguments', size='int'),
                             elm)

        id, act=self.ctxt.encode(fld)

        exp=('\xFD\x00\x01\x20\x05test1\x05' # struct test { w/ 5 members
        +'\xFD\x00\x02\x20\x09timeStamp\x02' # struct timeStamp { w/ 2 members
        +'\x04\x10secondsPastEpoch' # long secondsPastEpoch;
        +'\x03\x0bnanoSeconds' # int nanoSeconds; }
        +'\xFD\x00\x03\x30\x05value\x00\x02' # struct value[] { w/ 2 members
        +'\x06\x05value' # double value;
        +'\xFD\x00\x04\x20\x08location\x02' # struct location { w/ 2 members
        +'\x06\x01x' +'\x06\x01y' # double x, y; } }
        +'\x07\x0AfactoryRPC' # string factoryRPC;
        +'\xFD\x00\x05\x20\x09arguments\x01' # struct arguments { w/ 1 member
        +'\x03\x04size' # int size; }
        +'\xFD\x00\x06\x20\x07element\x03' # struct element { w/ 3 members
        +'\x06\x05value' # double value;
        +'\xFD\x00\x07\x20\x05alarm\x02' # struct alarm { w/ 2 members
        +'\x03\x08severity' # int severity;
        +'\x07\x07message' # string message; }
        +'\xFE\x00\x02' # struct timpStamp {...} } }
        )

        if act!=exp:
            print fld
            
        self.assertEqual(act, exp)
