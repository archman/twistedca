
TwCA.util.ifinspect - Network Interface Introspection
=====================================================

There is not general or OS independent mechanism for finding information about
the network interfaces present on the host computer.  This module therefore
takes the approach of selecting one of the available mechanisms based on
the host OS.  All access is through the :func:`getifinfo` function.

.. automodule:: TwCA.util.ifinspect
   :members:

Unix Systems
------------

On unix-like systems (including Linux) the :c:func:`ioctl` system call is used.
The flags :c:macro:`SIOCGIFCONF`, :c:macro:`SIOCGIFFLAGS`, and :c:macro:`SIOCGIFBRDADDR` are queried.

.. automodule:: TwCA.util.ifinspect.unix
   :members:

Windows Systems
---------------

For Windows systems the :c:func:`WSAIoctl` call is used with the :c:macro:`SIO_GET_INTERFACE_LIST` attribute.
This is listed as
`supported`_
on Windows 98, NT 4.0 (w/ SP4), and all later versions.

.. _supported: http://msdn.microsoft.com/en-us/library/ms741621%28v=vs.85%29.aspx

.. automodule:: TwCA.util.ifinspect.win32
   :members: win32
