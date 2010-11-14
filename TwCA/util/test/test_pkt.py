# -*- coding: utf-8 -*-

import unittest

from TwCA.util.ca import CAmessage, CAIncomplete

class TestXCode(unittest.TestCase):

    def test_normal(self):
        data=[
          ('\x00'*16,
           CAmessage()),
          ('\x00\x01\x00\x00\x00\x02\x00\x03\x00\x04\x00\x05\x00\x06\x00\x07',
           CAmessage(cmd=1, size=0, dtype=2, count=3, p1=0x40005, p2=0x60007)),
          ('\x00\x01\x00\x08\x00\x02\x00\x03\x00\x04\x00\x05\x00\x06\x00\x07'
           +'hello w\x00',
           CAmessage(cmd=1, size=8, dtype=2, count=3, p1=0x40005, p2=0x60007,
                     body='hello w\x00')),
        ]

        for raw, cook in data:
            raw2=cook.pack()
            self.assertEqual(raw, raw2)
            cook2, rem=CAmessage.unpack(raw)
            self.assertEqual(cook, cook2)
            self.assertEqual(len(rem), 0)

    def test_short(self):
        pkt='\x00\x01\x00\x10\x00\x02\x00\x03\x00\x04\x00\x05\x00\x06\x00\x07'

        self.assertRaises(CAIncomplete, CAmessage.unpack, pkt)

    def test_two(self):
        """Unpack two packets from the same buffer
        """
        msg1='\x00\x01\x00\x08\x00\x02\x00\x03\x00\x04\x00\x05\x00\x06\x00\x07' \
             'hello w\x00'
        msg2='\x00\x02\x00\x00\x00\x02\x00\x03\x00\x04\x00\x05\x00\x06\x00\x07'
        msg3='testing'
        buf=msg1+msg2+msg3

        exp1=CAmessage(cmd=1, size=8, dtype=2, count=3, p1=0x40005, p2=0x60007,
                       body='hello w\x00')
        exp2=CAmessage(cmd=2, size=0, dtype=2, count=3, p1=0x40005, p2=0x60007)

        pkt1, rem=CAmessage.unpack(buf)

        self.assertEqual(pkt1, exp1)
        self.assertEqual(rem, buffer(msg2+msg3))

        pkt2, rem=CAmessage.unpack(rem)
        self.assertEqual(pkt2, exp2)

        self.assertEqual(rem, buffer(msg3))
