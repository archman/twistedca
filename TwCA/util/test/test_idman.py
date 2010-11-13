# -*- coding: utf-8 -*-

from weakref import ref

from twisted.trial import unittest
from twisted.internet.defer import gatherResults, CancelledError

from TwCA.util.idman import *
 
class Counter(object):
    v=0

class TestManagers(unittest.TestCase):
    
    def test_idman(self):
        
        man=IDManager()
        
        self.assertEqual(len(man), 0)
        
        i=man.add(5)
        
        self.assertEqual(man[i], 5)
        
        self.assertTrue(i in man)
        
        def x():
            man[i]=6
        self.assertRaises(KeyError, x)

        j=man.add(5)
        
        self.assertEqual(man[j], 5)
        
        self.assertNotEqual(i, j)

        man.remove(i)
        
        self.assertTrue(i not in man)
        
        man._next=i # manually force reset
        
        k=man.add(6)

        self.assertEqual(i, k)

        l=man.add(7)

        self.failIfIn(k, (j, l))

    
    def test_cbman(self):

        C=Counter()

        man=CBManager()
        
        @man.add
        def cb(pos, kw=1):
            C.v+=kw

        man(42)

        self.assertEqual(C.v, 1)

        man(43, kw=5)

        self.assertEqual(C.v, 6)
        C.v=0

        def cb(_, kw=0, extra=4):
            C.v+=kw+extra

        man.add(cb, extra=3)
        self.assertRaises(AssertionError, man.add, cb, extra=2)

        self.assertEqual(len(man), 2)

        man(44, kw=-1)

        self.assertEqual(C.v, 1)
        C.v=0

    def test_defmanager(self):

        C=Counter()
        
        man=DeferredManager()
        
        self.assertRaises(NotImplementedError, man.add, 4)
        
        ds=[man.get() for i in range(4)]

        d=gatherResults(ds)
        
        def match(results):
            C.v+=1
            self.assertTrue(all(map(lambda x:x==5, results)))
            return results

        d.addCallback(match)

        e=man.get()
        @e.addCallback
        def x(_):
            C.v+=100
        @e.addErrback
        def E(err):
            err.trap(CancelledError)

        e.cancel()
        self.assertNotIn(e, man)

        man.callback(5)

        self.assertEqual(C.v, 1)

        d.addCallback(match)

        self.assertEqual(C.v, 2)
        
        man=DeferredManager()
        C.v=0

        d=man.get()
        d.addCallback(lambda _:self.fail())

        @d.addErrback
        def err(fail):
            C.v+=1
            self.assertEqual(fail.check(RuntimeError), RuntimeError)
            return fail

        man.get().addErrback(lambda e:e.trap(RuntimeError))

        try:
            raise RuntimeError('test')
        except:
            man.errback()

        self.assertEqual(C.v, 1)

        @d.addErrback
        def sink(fail):
            C.v+=1
            self.assertEqual(fail.trap(RuntimeError), RuntimeError)

        self.assertEqual(C.v, 2)

    def test_defmanagerRefs(self):
        """Check that deferred manager doesn't keep references
        """

        man=DeferredManager()

        class X(object):
            v=None
            def assign(self,x):
                self.v=x

        x=X()
        check=ref(x)

        d=man.get()
        d.addCallback(x.assign)
        d.addErrback(lambda e:e.trap(CancelledError))

        del x
        self.assertTrue(check() is not None)

        d.cancel()

        self.assertTrue(check() is None)

        y=X()
        check=ref(y)

        e=man.get()
        e.addCallback(y.assign)

        del y
        self.assertTrue(check() is not None)

        man.callback(0)

        self.assertTrue(check() is None)

