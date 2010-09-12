# -*- coding: utf-8 -*-

from struct import Struct

# status, severity, value
dbr_sts_string=Struct('!hh40s')
dbr_sts_int=Struct('!hhh')
dbr_sts_short=dbr_sts_int
dbr_sts_float=Struct('!hhf')
dbr_sts_enum=dbr_sts_int
dbr_sts_char=Struct('!hhxB')
dbr_sts_long=Struct('!hhi')
dbr_sts_double=Struct('!hhxxxxd')

# status, severity, ts_sec, ts_nsec, value
dbr_time_string=Struct('!hhII40s')
dbr_time_short=Struct('!hhIIxxh')
dbr_time_int=dbr_time_short
dbr_time_float=Struct('!hhIIf')
dbr_time_enum=dbr_time_short
dbr_time_char=Struct('!hhIIxxxB')
dbr_time_long=Struct('!hhIIi')
dbr_time_double=Struct('!hhIIxxxxd')

# status, severity, units, dU, dL, aU, wU, wL, aL, value
dbr_gr_int=Struct('!hh8shhhhhhh')
dbr_gr_short=dbr_gr_int
dbr_gr_char=Struct('!hh8sccccccxc')
dbr_gr_long=Struct('!hh8siiiiiii')

# status, severity, precision, units, dU, dL, aU, wU, wL, aL, value
dbr_gr_float=Struct('!hhhxx8sfffffff')
dbr_gr_double=Struct('!hhhxx8sddddddd')

# status, severity, #strings, 26x enum strings, value
dbr_gr_enum=Struct('!hhh' + '16c'*26 + 'H')

# status, severity, units, dU, dL, aU, wU, wL, aL, cU, cL, value
dbr_ctrl_int=Struct('!hh8shhhhhhhhh')
dbr_ctrl_short=dbr_ctrl_int
dbr_ctrl_char=Struct('!hh8sccccccccxc')
dbr_ctrl_long=Struct('!hh8siiiiiiiii')

# status, severity, precision, units, dU, dL, aU, wU, wL, aL, cU, cL, value
dbr_ctrl_float=Struct('!hhhxx8sfffffffff')
dbr_ctrl_double=Struct('!hhhxx8sddddddddd')

dbr_ctrl_enum=dbr_gr_enum

# Special

# status, severity, ackt, acks, value
dbr_stsack_string=Struct('!HHHH40s')
