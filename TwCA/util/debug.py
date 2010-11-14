
#
# Adapted from
#
# http://senzala.epx.com.br/2009/01/hunting-leaked-objects-in-python.html
#

import types
from warnings import warn
try:
    import gc
except ImportError:
    gc=None

_method_types=[types.BuiltinMethodType,
             types.MethodType,
            ]
_ignore_types=[types.BuiltinFunctionType,
               types.FunctionType,
#               types.FrameType,
              ]

def showRefs(obj, N=5, backrefs=set(), objs=None, P=''):
    """Given any Python object
    print a tree view of the objects which reference it.
    """
    if N<=0:
        return
    if gc is None:
        warn('GC debugging not enabled')
        return

    if objs is None:
        gc.collect()
        # list current objects
        # so we can reject temporaries created
        # by this function
        O=gc.get_objects()
        objs=[id(o) for o in O]

    if id(obj) in backrefs:
        return
    backrefs.add(id(obj))

    print P,'obj:',str(obj)[:60]
    print P,'typ:',type(obj)

    if obj in gc.garbage:
        print P,'  Uncollectable!'

    for ref in gc.get_referrers(obj):
        t=type(ref)
        if id(ref) in backrefs:
            print P,' <',str(ref)[:60]
            continue

        elif id(ref) not in objs:
            continue

        elif t in _method_types:
            backrefs.add(id(ref))
            print P,' >',str(ref)[:60]
            #for b in gc.get_referents(ref):
                #showRefs(b, N-1, backrefs, objs, P+'|')

        elif t in _ignore_types:
            pass

        elif t is types.FrameType:
            import inspect
            fname, line, func, ctxt, idx = inspect.getframeinfo(ref)
            if func=='showRefs':
                continue
            print P,' <<<'
            for f in inspect.getouterframes(ref):
                _, fname, line, func, ctxt, idx = f
                print P,'    %s()  %s:%d'%(func,fname,line)
            #fname, line, func, ctxt, idx = inspect.getframeinfo(ref)
            #print P,' F %s()  %s:%d'%(func,fname,line)

        elif hasattr(ref, '__class__'):
            if ref.__class__ in [list, dict, set, tuple]:
                if ref.__class__ is dict:
                    print P,' /--is:',
                    for k,v in ref.iteritems():
                        if v is obj:
                            print k,
                    print
                showRefs(ref, N-1, backrefs, objs, P+'.')
            else:
                print P,'  ',str(ref)[:60]

        else:
            print P,' ?',str(ref)[:60]
