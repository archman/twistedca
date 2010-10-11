# -*- coding: utf-8 -*-

from enum import Enum

__all__=['SERVER_PORT','CLIENT_PORT','CA_VERSION',
         'POSIX_TIME_AT_EPICS_EPOCH',
         'DBE','META','DBF','DBR','METAPARTS',
         'SEVERITY','STATUS',
         'dbf_elem_size',
         'dbr_to_dbf',
         'dbf_to_dbr']

SERVER_PORT=5064
CLIENT_PORT=5065

CA_VERSION=13

POSIX_TIME_AT_EPICS_EPOCH=631152000L

DBE=Enum('DBE.',VALUE=1, ARCHIVE=2, LOG=2, ALARM=4, PROPERTY=8)

# metadata parts
METAPARTS=Enum('METAPARTS.',
               NONE=0x00,
               STS =0x01, # sts, sev
               TIME=0x02, # stamp
               ENUM=0x04, # strs
               REAL=0x08, # precision
               GR  =0x10, # display, warn, alarm
               CTRL=0x20, # control
               SPEC=0x80, # special
              )

# metadata classes
META=Enum('META.',
          PLAIN=METAPARTS.NONE,
          STS=METAPARTS.STS,
          TIME=METAPARTS.STS|METAPARTS.TIME,
          GR=METAPARTS.STS|METAPARTS.GR,
          CTRL=METAPARTS.STS|METAPARTS.GR|METAPARTS.CTRL,
         )

# DBF and DBR types from db_access.h

DBF=Enum('DBF.',STRING=0, INT=1, SHORT=1, FLOAT=2,
                ENUM=3, CHAR=4, LONG=5, DOUBLE=6)

_elementsize={DBF.STRING:40,
              DBF.INT   :2,
              DBF.SHORT :2,
              DBF.FLOAT :4,
              DBF.ENUM  :2,
              DBF.CHAR  :1,
              DBF.LONG  :4,
              DBF.DOUBLE:8
             }
def dbf_elem_size(dbf):
    return _elementsize[dbf]

DBR=Enum('DBR.',
    STRING =DBF.STRING,
    INT    =DBF.INT,
    SHORT  =DBF.INT,
    FLOAT  =DBF.FLOAT,
    ENUM   =DBF.ENUM,
    CHAR   =DBF.CHAR,
    LONG   =DBF.LONG,
    DOUBLE =DBF.DOUBLE,
    STS_STRING =7,
    STS_SHORT  =8,
    STS_INT    =8, # dup
    STS_FLOAT  =9,
    STS_ENUM   =10,
    STS_CHAR   =11,
    STS_LONG   =12,
    STS_DOUBLE =13,
    TIME_STRING=14,
    TIME_INT   =15,
    TIME_SHORT =15, # dup
    TIME_FLOAT =16,
    TIME_ENUM  =17,
    TIME_CHAR  =18,
    TIME_LONG  =19,
    TIME_DOUBLE=20,
    GR_STRING  =21,
    GR_SHORT   =22,
    GR_INT     =22, # dup
    GR_FLOAT   =23,
    GR_ENUM    =24,
    GR_CHAR    =25,
    GR_LONG    =26,
    GR_DOUBLE  =27,
    CTRL_STRING=28,
    CTRL_SHORT =29,
    CTRL_INT   =29, # dup
    CTRL_FLOAT =30,
    CTRL_ENUM  =31,
    CTRL_CHAR  =32,
    CTRL_LONG  =33,
    CTRL_DOUBLE=34,
    PUT_ACKT   =35,
    PUT_ACKS   =36,
    STSACK_STRING=37,
    CLASS_NAME=38,
)

_DBR2DBF={
    DBR.STRING       :(DBF.STRING,META.PLAIN),
    DBR.INT          :(DBF.INT,   META.PLAIN),
    DBR.SHORT        :(DBF.INT,   META.PLAIN),
    DBR.FLOAT        :(DBF.FLOAT, META.PLAIN),
    DBR.ENUM         :(DBF.ENUM,  META.PLAIN),
    DBR.CHAR         :(DBF.CHAR,  META.PLAIN),
    DBR.LONG         :(DBF.LONG,  META.PLAIN),
    DBR.DOUBLE       :(DBF.DOUBLE,META.PLAIN),
    DBR.STS_STRING   :(DBF.STRING,META.STS),
    DBR.STS_SHORT    :(DBF.SHORT, META.STS),
    DBR.STS_INT      :(DBF.INT,   META.STS),
    DBR.STS_FLOAT    :(DBF.FLOAT, META.STS),
    DBR.STS_ENUM     :(DBF.ENUM,  META.STS),
    DBR.STS_CHAR     :(DBF.CHAR,  META.STS),
    DBR.STS_LONG     :(DBF.LONG,  META.STS),
    DBR.STS_DOUBLE   :(DBF.DOUBLE,META.STS),
    DBR.TIME_STRING  :(DBF.STRING,META.TIME),
    DBR.TIME_INT     :(DBF.INT,    META.TIME),
    DBR.TIME_SHORT   :(DBF.SHORT,  META.TIME),
    DBR.TIME_FLOAT   :(DBF.FLOAT,  META.TIME),
    DBR.TIME_ENUM    :(DBF.ENUM,   META.TIME),
    DBR.TIME_CHAR    :(DBF.CHAR,   META.TIME),
    DBR.TIME_LONG    :(DBF.LONG,   META.TIME),
    DBR.TIME_DOUBLE  :(DBF.DOUBLE,META.TIME),
    DBR.GR_STRING    :(DBF.STRING, META.STS),
    DBR.GR_SHORT     :(DBF.SHORT, META.GR),
    DBR.GR_INT       :(DBF.INT,      META.GR),
    DBR.GR_FLOAT     :(DBF.FLOAT, META.GR),
    DBR.GR_ENUM      :(DBF.ENUM,     META.GR),
    DBR.GR_CHAR      :(DBF.CHAR,     META.GR),
    DBR.GR_LONG      :(DBF.LONG,     META.GR),
    DBR.GR_DOUBLE    :(DBF.DOUBLE,META.GR),
    DBR.CTRL_STRING  :(DBF.STRING, META.STS),
    DBR.CTRL_SHORT   :(DBF.SHORT,  META.CTRL),
    DBR.CTRL_INT     :(DBF.INT,    META.CTRL),
    DBR.CTRL_FLOAT   :(DBF.FLOAT,  META.CTRL),
    DBR.CTRL_ENUM    :(DBF.ENUM,   META.GR),
    DBR.CTRL_CHAR    :(DBF.CHAR,   META.CTRL),
    DBR.CTRL_LONG    :(DBF.LONG,   META.CTRL),
    DBR.CTRL_DOUBLE  :(DBF.DOUBLE,META.CTRL),
    DBR.PUT_ACKT     :(DBF.SHORT,META.PLAIN),
    DBR.PUT_ACKS     :(DBF.SHORT,META.PLAIN),
    DBR.STSACK_STRING:(DBR.STSACK_STRING,None),
    DBR.CLASS_NAME   :(DBF.STRING,META.PLAIN),
}
def dbr_to_dbf(dbr):
    return _DBR2DBF[dbr]

# compute reverse mapping
_DBF2DBR={}
for k,v in _DBR2DBF.iteritems():
    if v[0] is None:
        continue
    if v in _DBF2DBR and k >= _DBF2DBR[v]:
        continue # for dups use lower
    _DBF2DBR[v]=k
# duplicates and special cases
for dup, src in [((DBF.STRING, META.CTRL),DBR.STS_STRING),
                 ((DBF.STRING, META.GR),  DBR.STS_STRING),
                 ((DBF.ENUM,   META.CTRL),DBR.GR_ENUM),
                ]:
    assert dup not in _DBF2DBR
    _DBF2DBR[dup]=src
def dbf_to_dbr(dbf, meta):
    return _DBF2DBR[(dbf, meta)]

SEVERITY=Enum('', NO_ALARM=0, MINOR=1, MAJOR=2, INVALID=3)

STATUS=Enum('', NONE=0, READ=1, WRITE=2,
                HIHI=3, HIGH=4, LOLO=5, LOW=6,
                STATE=7, COS=8, COMM=9, TIMEOUT=10,
                HW_LIMIT=11, CALC=12, SCAN=13, LINK=14,
                SOFT=15, BAD_SUB=16, UDF=17, DISABLE=18,
                SIMM=19, READ_ACCESS=20, WRITE_ACCESS=21
            )
