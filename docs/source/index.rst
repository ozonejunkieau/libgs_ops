.. libgs-ops documentation master file, on 13 Dec 2018
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


.. container:: License

 Copyright © 2017-2018 The University of New South Wales
 Copyright © 2019 Kjetil Wormnes

 Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

 Except as contained in this notice, the name or trademarks of a copyright holder shall not be used in advertising or otherwise to promote the sale, use or other dealings in this Software without prior written authorization of the copyright holder.

 UNSW is a trademark of The University of New South Wales.


Welcome to the documentation for libgs ops
==========================================

libgs-ops is a library for planning satellite passes and then creating schedules that can be executed on a libgs-based ground station.

It consists of 2 main modules; the propagator module is a generic pyephem based library for analysing orbits and planning passes, 
whereas scheduling is aimed at making libgs-compatible communication schedules.


Installation
-------------

libgs-ops is fairly light on requirements and should be possible to run on any rasonable python installation.

.. note::

   python3 support is planned and should not pose any great difficulty to implement. It has however not been prioritised up to
   this point as no users have expressed strong need for it.

.. warning::

   If you are reading this on readthedocs, the documentation is most likely broken.
   So until I succeed in getting it to play nice with RTD (i.e. until further notice), it will be hosted
   on github pages and you can access it at the following address:

   https://kworm1.github.io/libgs-docs/


API reference by module
-------------------------

.. autosummary::
    :toctree: _autosummary

    libgs_ops.propagator
    libgs_ops.scheduling
    libgs_ops.rpc
