#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
import asyncore
from util import timer

class TestShutdown(unittest.TestCase):
    """Ensure that the timer Queue stops
    when it should
    """
    class stop(timer.Timer):
        def __init__(self,*args, **kwargs):
            timer.Timer.__init__(self,*args, **kwargs)
            self.C=False
        def cancelled(self):
            self.C=True

    def tearDown(self):
        asyncore.close_all()

    def test_null(self):
        """Destroy a queue as soon as
        it is created.
        """
        Q=timer.Queue()
        self.assertFalse(Q.closed)
        Q.close()
        self.assertTrue(Q.closed)
        
        asyncore.loop() # should end immediately

    def test_immediate(self):
        Q=timer.Queue()
        t=self.stop(Q)
        t.set_single(99999.0)
        
        self.assertEqual(Q.next, t)
        self.assertFalse(t.C)
        
        self.assertFalse(Q.closed)
        Q.close()
        self.assertTrue(Q.closed)
        
        self.assertEqual(Q.next, None)
        self.assertTrue(t.C)

        asyncore.loop() # should end immediately

    def test_deferred(self):        
        Q=timer.Queue()
        t=self.stop(Q)
        t.set_single(99999.0)
        
        self.assertEqual(Q.next, t)
        self.assertFalse(t.C)

        asyncore.loop(count=1)
        
        self.assertEqual(Q.next, t)
        self.assertFalse(t.C)

        self.assertFalse(Q.closed)
        Q.close()
        self.assertTrue(Q.closed)
        
        self.assertEqual(Q.next, None)
        self.assertTrue(t.C)

        asyncore.loop() # should end immediately

    def test_fromcallback(self):
        def stop(t):
            t.Q.close()

        Q=timer.Queue()
        t=timer.Timer(Q, stop)
        t.set_single(0.0)

        self.assertFalse(Q.closed)
        asyncore.loop()
        self.assertTrue(Q.closed)

    def test_fromdelaycallback(self):
        def stop(t):
            t.Q.close()

        Q=timer.Queue()
        t=timer.Timer(Q, stop)
        t.set_single(1.0)

        self.assertFalse(Q.closed)
        asyncore.loop()
        self.assertTrue(Q.closed)


class TestDeadline(unittest.TestCase):
    
    def setUp(self):
        self.Q=timer.Queue()

    def tearDown(self):
        asyncore.close_all()

    def startTimers(self, times):
        import time
        self.Q.val=len(times)
        def count(t, test, expected):
            now=time.time()
            t.Q.val=t.Q.val-1
            test.assertTrue(now >= expected)
            if t.Q.val==0:
                t.Q.close()


        now=time.time()
        for t in times:
            a=timer.Timer(self.Q, count, args=(self,now+t))
            a.set_single(t)

        self.assertEqual(self.Q.val, len(times))

        asyncore.loop()

        self.assertEqual(self.Q.val, 0)

    def test_postinorder(self):
        times=[0.0, 0.2, 0.4, 1.3]
        self.startTimers(times)

    def test_outoforder(self):
        times=[0.4, 0.4, 0.2, 0.0, 1.3]
        self.startTimers(times)

    def test_rearm(self):
        self.Q.val=5
        def count(t):
            t.Q.val=t.Q.val-1
            if t.Q.val!=0:
                t.set_single(0.1)
            else:
                t.Q.close()
        
        t=timer.Timer(self.Q, count)
        t.set_single(0.1)

        self.assertEqual(self.Q.val, 5)

        asyncore.loop()

        self.assertEqual(self.Q.val, 0)

if __name__ == '__main__':
    import logging
    logging.basicConfig(format='%(message)s',level=logging.DEBUG)
    unittest.main()
