# -*- coding: utf-8 -*-

class CAError(Exception):
    def __init__(self, msg, code):
        self.msg=msg
        self.code
    def __str__(self):
        return 'CAError: '+str(self.msg)
        
# the following derived from caerr.h in Base

CA_K_INFO      =3   # successful
CA_K_ERROR     =2   # failed- continue
CA_K_SUCCESS   =1   # successful
CA_K_WARNING   =0   # unsuccessful
CA_K_SEVERE    =4   # failed- quit
CA_K_FATAL =CA_K_ERROR | CA_K_SEVERE

CA_M_MSG_NO    =0x0000FFF8
CA_M_SEVERITY  =0x00000007
CA_M_LEVEL     =0x00000003
CA_M_SUCCESS   =0x00000001
CA_M_ERROR     =0x00000002
CA_M_SEVERE    =0x00000004

CA_S_MSG_NO    =0x0D
CA_S_SEVERITY  =0x03

CA_V_MSG_NO    =0x03
CA_V_SEVERITY  =0x00
CA_V_SUCCESS   =0x00

def CA_EXTRACT_MSG_NO(code):
    return ( code & CA_M_MSG_NO ) >> CA_V_MSG_NO
def CA_EXTRACT_SEVERITY(code):
    return ( code & CA_M_SEVERITY )>> CA_V_SEVERITY
def CA_EXTRACT_SUCCESS(code):
    return ( code & CA_M_SUCCESS )>> CA_V_SUCCESS

def CA_INSERT_MSG_NO(code):
    return (code<< CA_V_MSG_NO) & CA_M_MSG_NO
def CA_INSERT_SEVERITY(code):
    return (code<< CA_V_SEVERITY)& CA_M_SEVERITY
def CA_INSERT_SUCCESS(code):
    return (code<< CA_V_SUCCESS) & CA_M_SUCCESS

def DEFMSG(SEVERITY,NUMBER):
    return CA_INSERT_MSG_NO(NUMBER) | CA_INSERT_SEVERITY(SEVERITY)

# In the lines below "defunct" indicates that current release 
# servers and client library will not return this error code, but
# servers on earlier releases that communicate with current clients 
# might still generate exceptions with these error constants

ECA_NORMAL         =DEFMSG(CA_K_SUCCESS,    0) # success
ECA_MAXIOC         =DEFMSG(CA_K_ERROR,      1) # defunct
ECA_UKNHOST        =DEFMSG(CA_K_ERROR,      2) # defunct
ECA_UKNSERV        =DEFMSG(CA_K_ERROR,      3) # defunct
ECA_SOCK           =DEFMSG(CA_K_ERROR,      4) # defunct
ECA_CONN           =DEFMSG(CA_K_WARNING,    5) # defunct
ECA_ALLOCMEM       =DEFMSG(CA_K_WARNING,    6) 
ECA_UKNCHAN        =DEFMSG(CA_K_WARNING,    7) # defunct
ECA_UKNFIELD       =DEFMSG(CA_K_WARNING,    8) # defunct
ECA_TOLARGE        =DEFMSG(CA_K_WARNING,    9) 
ECA_TIMEOUT        =DEFMSG(CA_K_WARNING,   10)
ECA_NOSUPPORT      =DEFMSG(CA_K_WARNING,   11) # defunct
ECA_STRTOBIG       =DEFMSG(CA_K_WARNING,   12) # defunct
ECA_DISCONNCHID    =DEFMSG(CA_K_ERROR,     13) # defunct
ECA_BADTYPE        =DEFMSG(CA_K_ERROR,     14)
ECA_CHIDNOTFND     =DEFMSG(CA_K_INFO,      15) # defunct
ECA_CHIDRETRY      =DEFMSG(CA_K_INFO,      16) # defunct
ECA_INTERNAL       =DEFMSG(CA_K_FATAL,     17)
ECA_DBLCLFAIL      =DEFMSG(CA_K_WARNING,   18) # defunct
ECA_GETFAIL        =DEFMSG(CA_K_WARNING,   19)
ECA_PUTFAIL        =DEFMSG(CA_K_WARNING,   20)
ECA_ADDFAIL        =DEFMSG(CA_K_WARNING,   21) # defunct
ECA_BADCOUNT       =DEFMSG(CA_K_WARNING,   22)
ECA_BADSTR         =DEFMSG(CA_K_ERROR,     23)
ECA_DISCONN        =DEFMSG(CA_K_WARNING,   24)
ECA_DBLCHNL        =DEFMSG(CA_K_WARNING,   25)
ECA_EVDISALLOW     =DEFMSG(CA_K_ERROR,     26)
ECA_BUILDGET       =DEFMSG(CA_K_WARNING,   27) # defunct
ECA_NEEDSFP        =DEFMSG(CA_K_WARNING,   28) # defunct
ECA_OVEVFAIL       =DEFMSG(CA_K_WARNING,   29) # defunct
ECA_BADMONID       =DEFMSG(CA_K_ERROR,     30)
ECA_NEWADDR        =DEFMSG(CA_K_WARNING,   31) # defunct
ECA_NEWCONN        =DEFMSG(CA_K_INFO,      32) # defunct
ECA_NOCACTX        =DEFMSG(CA_K_WARNING,   33) # defunct
ECA_DEFUNCT        =DEFMSG(CA_K_FATAL,     34) # defunct
ECA_EMPTYSTR       =DEFMSG(CA_K_WARNING,   35) # defunct
ECA_NOREPEATER     =DEFMSG(CA_K_WARNING,   36) # defunct
ECA_NOCHANMSG      =DEFMSG(CA_K_WARNING,   37) # defunct
ECA_DLCKREST       =DEFMSG(CA_K_WARNING,   38) # defunct
ECA_SERVBEHIND     =DEFMSG(CA_K_WARNING,   39) # defunct
ECA_NOCAST         =DEFMSG(CA_K_WARNING,   40) # defunct
ECA_BADMASK        =DEFMSG(CA_K_ERROR,     41)
ECA_IODONE         =DEFMSG(CA_K_INFO,      42)
ECA_IOINPROGRESS   =DEFMSG(CA_K_INFO,      43)
ECA_BADSYNCGRP     =DEFMSG(CA_K_ERROR,     44)
ECA_PUTCBINPROG    =DEFMSG(CA_K_ERROR,     45)
ECA_NORDACCESS     =DEFMSG(CA_K_WARNING,   46)
ECA_NOWTACCESS     =DEFMSG(CA_K_WARNING,   47)
ECA_ANACHRONISM    =DEFMSG(CA_K_ERROR,     48)
ECA_NOSEARCHADDR   =DEFMSG(CA_K_WARNING,   49)
ECA_NOCONVERT      =DEFMSG(CA_K_WARNING,   50)
ECA_BADCHID        =DEFMSG(CA_K_ERROR,     51)
ECA_BADFUNCPTR     =DEFMSG(CA_K_ERROR,     52)
ECA_ISATTACHED     =DEFMSG(CA_K_WARNING,   53)
ECA_UNAVAILINSERV  =DEFMSG(CA_K_WARNING,   54)
ECA_CHANDESTROY    =DEFMSG(CA_K_WARNING,   55)
ECA_BADPRIORITY    =DEFMSG(CA_K_ERROR,     56)
ECA_NOTTHREADED    =DEFMSG(CA_K_ERROR,     57)
ECA_16KARRAYCLIENT =DEFMSG(CA_K_WARNING,   58)
ECA_CONNSEQTMO     =DEFMSG(CA_K_WARNING,   59)
ECA_UNRESPTMO      =DEFMSG(CA_K_WARNING,   60)

# user code should not care about these
del CA_EXTRACT_MSG_NO
del CA_EXTRACT_SEVERITY
del CA_EXTRACT_SUCCESS
del CA_INSERT_MSG_NO
del CA_INSERT_SEVERITY
del CA_INSERT_SUCCESS
del DEFMSG
