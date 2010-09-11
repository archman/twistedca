#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Timer queue for asyncore

Implements efficient waiting and dispatch
of multiple timers on a single queue.
"""

import asyncore, socket, time, logging

log = logging.getLogger('util.timer')

__all__ = ['Timer','Queue']

class Timer(object):
    
    def __init__(self, queue, target=None, args=()):
        self._queue=queue
        self._cancel()
        self._target=target
        self._args=args

    @property
    def Q(self):
        return self._queue

    def expired(self):
        if self._target is not None:
            self._target(self, *self._args)

    def cancelled(self):
        pass

    def running(self):
        return self._expires_at is not None

    def cancel(self):
        self._cancel()
        self._queue.update(self)

    def _cancel(self):
        self._expires_at=None
        self._period=None

    def set_single(self, reltime):
        now=time.time()
        self._cancel()
        self._expires_at=now+reltime
        self._queue.update(self)

    def set_periodic(self, period, delay=None):
        now=time.time()
        self._cancel()
        self._period=period

        if delay is None:
            self._expires_at=now+period
        else:
            self._expires_at=now+delay
        self._queue.update(self)

    def __cmp__(self, O):
        assert self._expires_at is not None
        assert O._expires_at is not None
        return cmp(self._expires_at,O._expires_at)

    def __repr__(self):
        if self._period is None:
            return 'Deadline timer %f'%self._expires_at
        elif self._repeat is None:
            return 'Periodic timer %f in %f'% \
                (self._period,self._expires_at)
        else:
            return 'Periodic %d timer %f in %f'% \
                (self._repeat,self._period,self._expires_at)

class Queue(object):

    class endpoint(asyncore.dispatcher):
        """Proxy endpoint.
        
        This exists so that timer_queue does
        not have to export all of the members of
        a dispatcher
        """
        def __init__(self,Q,loc):
            asyncore.dispatcher.__init__(self, sock=loc)
            self.Q=Q
            log.debug('  Timer queue created')

        def writeable(self):
            """This end will only receive
            """
            return False

        def handle_read(self):
            self.recv(16)
            self.Q._dispatch()

        def handle_close(self):
            log.error('Timer queue thread died!')
            self.close()
    
    def __init__(self):
        import threading
        wakeup, loc = socket.socketpair()
        
        self._end=self.endpoint(self,loc)
        
        self._next_wakeup=None
        self._timers=[]
        self._started=threading.Event()
        
        self._sync=threading.Lock()
        self._wait=threading.Condition(self._sync)
        self._thrd=threading.Thread(target=self._sleeper,
                                    args=(wakeup,),
                                    name='TimerQueue')
        self._run=True
        self._thrd.start()
        self._started.wait()
        del self._started

    @property
    def closed(self):
        return not self._run

    def close(self):
        """Shut down the queue
        """
        # halt thread
        log.debug('  Timer queue shutdown start')
        self._wait.acquire()
        log.debug('A >>>>>>>>')
        self._run=False
        self._wait.notify()
        log.debug('A <<<<<<<<')
        self._wait.release()
        self._thrd.join()
        
        # cancel remaining timers
        for t in self._timers:
            t.cancelled()
        self._timers=[]
        self._next_wakeup=None

        # close socket
        self._end.close()
        log.debug('  Timer queue shutdown')

    @property
    def next(self):
        if len(self._timers)>0:
            return self._timers[0]
        else:
            return None

    def update(self, timer):
        log.debug('  update %s',repr(timer))

        now=time.time()

        if timer._expires_at is not None and timer not in self._timers:
            log.debug('  update add')
            self._timers.append(timer)

        elif timer._expires_at is None and timer in self._timers:
            log.debug('  update remove')
            self._timers.remove(timer)

        self._timers.sort()
        self._check_wakeup()

    def _check_wakeup(self):
        if len(self._timers)==0:
            next=None
        else:
            next = self._timers[0]._expires_at
        
        self._sync.acquire()
        log.debug('B >>>>>>>>')

        if next is not self._next_wakeup:
            log.debug('  poke!')
            self._wait.notify()

        self._next_wakeup = next
        log.debug('  next wakeup %s',repr(self._next_wakeup))

        log.debug('B <<<<<<<<')
        self._sync.release()

    def _dispatch(self):
        now=time.time()
        log.debug('  _dispath %f',now)
        while len(self._timers)>0 and self._timers[0]._expires_at <= now:
            t = self._timers.pop(0)
            log.debug('  _dispath expire')
            if t._period is not None:
                t._expires_at=t._expires_at + t._period
            else:
                t._expires_at=None
            t.expired()

        self._check_wakeup()

        log.debug('  _dispatch remaining %s',str(self._timers))

    def _sleeper(self, wakeup):
        self._wait.acquire()
        log.debug('C >>>>>>>>')
        
        self._started.set()
        log.debug('C <<<<<<<<')
        # Since the queue is initially empty
        # wait for the first wakeup
        self._wait.wait()
        log.debug('C >>>>>>>>')

        while self._run:
            log.debug('T Wakeup!')
            wakeup.send('X')

            next=self._next_wakeup
            if next is not None:
                next=next-time.time()
            if next<=0:
                next=None

            log.debug('T waiting for %s',str(next))
            log.debug('C <<<<<<<<')
            self._wait.wait(next)
            log.debug('C >>>>>>>>')

        log.debug('T Stop')
        wakeup.close()

        log.debug('C <<<<<<<<')
        self._wait.release()
