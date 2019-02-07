# -*- coding: utf-8 -*-
"""
..
    Copyright © 2017-2018 The University of New South Wales

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
    Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
    CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    Except as contained in this notice, the name or trademarks of a copyright holder

    shall not be used in advertising or otherwise to promote the sale, use or other
    dealings in this Software without prior written authorization of the copyright
    holder.

    UNSW is a trademark of The University of New South Wales.


libgs_ops.propagator
=====================

:date:   Jan  2 10:10:48 2018
:author: Kjetil Wormnes


libgs_ops.propagator has been designed to allow you to design and plan satellite passes, and to calculate the data required by
:mod:`.scheduling` when creating the Schedules to upload to the groundstation.

Usage
---------

You can use TLEs from a database with the TLEDb interface:

>>> p = Propagator(api=TLEDb('leo_tles.txt'), gs_lat = GS_LAT, gs_lon = GS_LON, gs_elev = GS_ELEV) #<-- replace path with a txt file of recent TLEs
>>> p.get_tle(25544)
('0 ISS (ZARYA)',
 '1 25544U 98067A   17330.99569027  .00003456  00000-0  59208-4 0  9997',
 '2 25544  51.6427 306.6944 0004138 155.0450 324.2726 15.54239375 87077')

.. note::
    This assumes the file leo_tles.txt exists, and is in the correct format. The file can contain many tles.
    You can download tles from Space-Track.org. They need to be in the 3le format.

A TLE that is not in the database will fail:

>>> p.get_tle(40000)
KeyError: 40000

Or you can connect directly to spacetrack if you have login credentials. Note hat uname, pwd are your Space-Track.org 
username and password. GS_LAT, GS_LON, GS_ELEV are the coordinates of your ground station.

>>> p = Propagator(api=SpaceTrackAPI(uname, pwd), gs_lat = GS_LAT, gs_lon = GS_LON, gs_elev = GS_ELEV)

Now we can get any TLE:

>>> [p.get_tle(25544), p.get_tle(40000)]
[('0 ISS (ZARYA)',
  '1 25544U 98067A   18191.92601852  .00011951  00000-0  18828-3 0  9990',
  '2 25544  51.6420 260.3859 0003584 301.4077  43.7815 15.54010757122205'),
 ('0 FENGYUN 2C DEB',
  '1 40000U 04042D   17363.55183407 -.00000332  00000-0  00000+0 0  9995',
  '2 40000   9.4060  40.1038 0077532 344.5713  15.1779  1.00303233 32417')]


Or you can even specify a TLE directly (only really useful for testing):

>>> tle = \"""0 ISS (ZARYA)
>>> 1 25544U 98067A   17284.88510854  .00004604  00000-0  76690-4 0  9997
>>> 2 25544  51.6422 176.5756 0004586  12.7905  64.0182 15.54151166 79907\"""
>>> p = Propagator(tles=tle, gs_lat = GS_LAT, gs_lon = GS_LON, gs_elev = GS_ELEV)


The propagator provides many utility functions to allow you to easily visualise and plan passes. For this example, we will 
work with the International Space Station (ISS) which has NORAD ID 25544. To print details about it, including
where  it is at the moment:

>>> p.print_info(25544)
TLE (updated 12/04/2018 09:56:44):
0 ISS (ZARYA)
    1 25544U 98067A   17284.88510854  .00004604  00000-0  76690-4 0  9997
    2 25544  51.6422 176.5756 0004586  12.7905  64.0182 15.54151166 79907
\
Orbit:
        epoch (utc) : 2017/10/11 21:14:33
        eccentricity: 0.000459
        inclindation: 51.642200
                RAAN: 176.575607
                  AP: 12.790500
       revol per day: 15.541512
  mean anom at epoch: 64.018204
   orbit no at epoch: 7990
\
Observer:
                 lat: -35.291447
                 lon: 149.165655
                elev: 614
          date (utc): 2018/04/11 23:56:55
\
Satellite:
    ground track pos: (lat = 33.998, lon = -179.991)
            pointing: (az  = 26.178, el  = -35.329)
               range: 7997806.500000
          range rate: 5306.109375
            altitude: 400772.000000
        orbit number: 10820.520789

We can compute the details of the next pass using :meth:`Propagator.compute_pass`. It returns two tables, pdat and psum. 
pdat includes deails about az, el and range_rate during the pass and is what the :class:`.Scheduler` will require (more about
that later), and psum shows an overview:

>>> pdat, psum = p.compute_pass(25544)
>>> psum

======= ======== ====================== =============== =========== =========== =============== =============== ============== ============ =========== ========
.       norad_id tstamp_str             orbit_no        az          el          range           range_rate      altitude       lat          long        eclipsed
======= ======== ====================== =============== =========== =========== =============== =============== ============== ============ =========== ========
rise    25544    2018/4/12 12:56:27     10828.934071     341.021182 0.017601    2.362804e+06    -6453.000000    404883.78125   -15.640039   142.408351  True
peak    25544    2018/4/12 13:01:33     10828.989114     50.446186  21.951227   9.426514e+05    57.450962       408999.65625   -30.219701   155.773119  True
set     25544    2018/4/12 13:06:40     10829.044337     118.978849 0.075523    2.383968e+06    6468.492188     413027.25000   -42.669076   173.889048  True
======= ======== ====================== =============== =========== =========== =============== =============== ============== ============ =========== ========

.. note::
    pdat (and psum) returns more information (columns) than are required by :class:`Schedule`, which only needs az, el and range_rate.

Most of the other functionality in this module are subsets of :meth:`Propagator.get_all`:

>>> p.get_all(25544)
norad_id                    25544
tstamp_str    2018/04/11 23:59:00
orbit_no                  10820.5
az                        28.9954
el                       -39.2531
range                 8.64443e+06
range_rate                5033.92
altitude                   402203
lat                       39.1371
long                     -172.682
eclipsed                    False
Name: 2018/04/11 23:59:00, dtype: object

You can provide a when=keyword to specify when you want the details computed for, or even an array of timestamps:

>>> p.get_all(25544, when=['2018/04/11 23:59:00', '2018/04/11 23:60:00', '2018/04/11 23:61:00'])

======================= ========= ==================== ========= ======== ========= ============ =========== ========= ======== ========= =========
.                       norad_id  tstamp_str           orbit_no  az       el        range        range_rate  altitude  lat      long      eclipsed
======================= ========= ==================== ========= ======== ========= ============ =========== ========= ======== ========= =========
2018/04/11 23:59:00     25544     2018/04/11 23:59:00  10820.5   28.9954  -39.2531  8.64443e+06  5033.92     402203    39.1371  -172.682  False
2018/04/11 23:60:00     25544     2018/04/11 23:60:00  10820.6   30.3388  -41.12    8.94222e+06  4891.28     402885    41.401   -168.776  False
2018/04/11 23:61:00     25544     2018/04/11 23:61:00  10820.6   31.6915  -42.9758  9.23124e+06  4741.58     403546    43.5045  -164.581  False
======================= ========= ==================== ========= ======== ========= ============ =========== ========= ======== ========= =========

A more complicated example to show how you can do anything you can do in python. 
Requires mplleaflet to be installed (pip install mplleaflet):

>>> import matplotlib.pyplot as plt
>>> import mplleaflet
>>> latlon = [p.get_ground_coord(25544, when=tstamp) for tstamp in pdat.tstamp_str]
>>> lat, lon = zip(*latlon)
>>> plt.plot(lon, lat, linewidth=3, color='r')
>>> plt.plot(p.gs_lon, p.gs_lat, 'ro', markersize=10)
>>> mplleaflet.display(tiles='esri_aerial')

It can be useful to get an overview of upcoming satellite passes. Just use :meth:`Propagator.get_passes` to very quickly calculate upcoming
passes. It also optionally accepts the ``when`` keyword in the same way as :meth:`Propagator.get_all` (if omitted when = Now) as well as ``N`` to specify the number
of upcoming passes to calculate (if omitted N=1), and ``horizon`` to filter by passes that are higher than a certain elevation. For example:

>>> p.get_passes([25544, 42778, 42017], N=1, horizon=10)

=== ======= ============= ======================= ============== ======================= ============= ======================= =============
.   nid     orbit_no      rise_t                  rise_az        max_elev_t              max_elev      set_t                   set_az
=== ======= ============= ======================= ============== ======================= ============= ======================= =============
0   42778   4451.856863   2018/04/12 11:00:07     150.894247     2018/04/12 11:05:31     18.542780     2018/04/12 11:10:50     19.517481
1   42017   6406.847362   2018/04/12 12:10:13     169.722360     2018/04/12 12:16:10     83.098219     2018/04/12 12:22:01     345.571864
2   25544   10832.568897  2018/04/12 14:03:15     308.388451     2018/04/12 14:08:46     69.318347     2018/04/12 14:14:22     133.721252
=== ======= ============= ======================= ============== ======================= ============= ======================= =============

.. note::
    The horizon parameter just filters the rows to show anything with max_elev > horizon. rise_t and set_t still correspond to horizon=0. 
    This is because get_passes uses a quick computation algorithm (See :meth:`ephem.Observer.next_pass`). To get the actual
    rise_t and set_t for that horizon, run :meth:`Propagator.compute_pass` with ``when`` set to the corresponding rise_t.


A common use of get_passes is to get the list of upcoming passes you want to create a schedule for. You then need to call compute_passes
for each of the rows in the get_passes table by giving the ``when`` parameter as the corresponding rise_t. The below example uses the
:func:`mpl_plot_pass` convenience function to plot a representation for each of the upcoming passes:

>>> for k,satpass in p.get_passes([25544, 42778, 42017], N=1, horizon=10).iterrows():
>>>     pdat, psum = p.compute_pass(satpass.nid, when=satpass.rise_t)   
>>>     mpl_plot_pass(pdat) 

Module reference
----------------

"""


import requests
import ephem
from datetime import datetime
import time
from math import pi
import pandas as pd
from pandas import DataFrame
import numpy as np
from lxml import html
import re
from functools import wraps


def _print( *arg, **kwarg):
    """
        Function to print.

        This wrapper funciton is provided to allow for more easy redirection
        of output to other destinations (including Bokeh GUI, or files) if
        necessary in the futrue.

        It should be used for information targeted at an interactive user, not
        for logging messages

    """

    print(*arg, **kwarg)



class Error(Exception):
    """ A generic exception """
    pass

try:
    import matplotlib.pyplot as plt
    _HAS_MATPLOTLIB = True
except:
    _HAS_MATPLOTLIB = False

from collections import Iterable

import logging
log = logging.getLogger('libgs_ops-log')
log.addHandler(logging.NullHandler())



# Decorator to more easily tag matplotlib functions
def _mpl(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not _HAS_MATPLOTLIB:
            raise Error("matplotib.pyplot not available, before using this funciton you need to install it : pip install matplotlib")
        else:
            func(*args, **kwargs)

    return wrapper



def _tstamp_array(start, end, dt=None):
    """
        Helper function to create an array of ephem.Date
    """
    t0 = ephem.Date(start)
    t1 = ephem.Date(end)

    if dt is None:
        t_array = np.linspace(t0,t1, 100)
    else:
        dt_days = dt/86400.0
        t_array = np.arange(t0,t1,dt_days)

    t_array2 = [ephem.Date(t) for t in t_array]

    return t_array2



@_mpl
def mpl_plot_pass(angs, vishor=10):
    """
    A helper function to plot a pass in polar coordinates.

    This function requires matplotlib to be installed.

    Args:
        angs:       The antenna angles (pandas dataframe with az+el columns)
        vishor:     The horizon (deg)

    Returns:
        None

    """

    angs = angs[angs.el>vishor]

    if angs.empty:
        raise Error("Pass never comes above visiblity horizon")

    plot_fig = plt.gcf()
    ax = plot_fig.add_subplot(111, projection='polar')
    ax.set_ylim([0,90])


    az = angs.az/180.0*pi
    el = 90 - angs.el

    ax.plot(az,el, 'b', linewidth=2)

    # plot visibility horizon
    min_el = vishor
    h_az = np.linspace(0,2*pi, 100)
    h_el = [90-min_el]*len(h_az)
    ax.plot(h_az, h_el, 'r')


    # print timestamps for start/end pass

    maxe = angs[angs.el == angs.el.max()]
    if type(maxe) == DataFrame:
        maxe = maxe.iloc[0]

    kaz = np.array([angs.iloc[0].az, maxe.az, angs.iloc[-1].az])
    kel = np.array([angs.iloc[0].el, maxe.el, angs.iloc[-1].el])
    kt  = np.array([angs.iloc[0].tstamp_str, maxe.tstamp_str, angs.iloc[-1].tstamp_str])

    ax.plot(kaz/180.0*pi, 90-kel, 'b.', markersize=10)
    for i in range(0, len(kaz)):
        ax.text(kaz[i]/180.0*pi, 90-kel[i], kt[i], color='b', weight='bold')


    ax.set_yticklabels([])
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)




class SpaceTrackAPI(object):
    """
        Class to interface with `space-track.org <https://www.space-track.org>`_.

        This class connects to the space-track.org public API, and therefore requires a username and password. 
        To obtain such credentials you can register for free on the space-track website.

        This class allows the execution of arbitrary API queries, but provides a simplified method to download TLEs in
        the format used by :class:`.Propagator`.
    """

    ST_URL='https://www.space-track.org'

    def __init__(self, uname, pwd):
        """
        :param uname: space-track.org user name
        :param pwd: space-track.org password
        """
        r=requests.post(self.ST_URL+"/ajaxauth/login", json={'identity':uname, 'password':pwd})

        #
        # Raise error if login request fails
        #
        r.raise_for_status()
        self.cookies = r.cookies

    def query_raw(self, uri):
        """
            Perform a raw query to spacetrack API. Can return anything the API
            can.

            See `spacetrack <https://www.space-track.org/documentation#/api>`_
            for the URI syntax.

            Args:
                uri (string): URI, starting with '/'. It will be appended to the
                spacetrack URL.

            Example:

            >>> query_raw('/basicspacedata/query/class/boxscore/format/csv')

            Will return Space Objects Box Score, part 1 of the Space Situation Report (SSR), in CSV format

        """

        r = requests.get(self.ST_URL+uri, cookies=self.cookies)
        r.raise_for_status()
        return r.content

    def query_tle(self, params):
        """
            Perform a (fairly) raw query to the spacetrack API for the most recent
            three-line-elements.

            Args:
                params (dict): A dictionary of parameter/argument pairs that
                    specify the exact query to make.

            .. Note::
                This function will always return three-line-elements. I.e.
                the param pairs are added to the API URI "/basicspacedata/query/class/tle_latest/format/3le/ORDINAL/1"



            **Parameter syntax**


            See `spacetrack <https://www.space-track.org/documentation#/api>`_
            for the most up-to-date descripions of the possible parameter/value pairs.

            Each entry in the param dict follows key:value as per the model
            definition. For the latest model definition see `here <https://www.space-track.org/basicspacedata/modeldef/class/tle_latest/format/html>`_.

            ===================== =========================
            Field                 Type
            ===================== =========================
            ORDINAL               tinyint(3) unsigned
            COMMENT               varchar(32)
            ORIGINATOR            varchar(5)
            NORAD_CAT_ID          mediumint(8) unsigned
            OBJECT_NAME           varchar(60)
            OBJECT_TYPE           varchar(11)
            CLASSIFICATION_TYPE   char(1)
            INTLDES               varchar(8)
            EPOCH                 datetime
            EPOCH_MICROSECONDS    mediumint(8) unsigned
            MEAN_MOTION           double
            ECCENTRICITY          double
            INCLINATION           double
            RA_OF_ASC_NODE        double
            ARG_OF_PERICENTER     double
            MEAN_ANOMALY          double
            EPHEMERIS_TYPE        tinyint(3) unsigned
            ELEMENT_SET_NO        smallint(5) unsigned
            REV_AT_EPOCH          float
            BSTAR                 double
            MEAN_MOTION_DOT       double
            MEAN_MOTION_DDOT      double
            FILE                  int(10) unsigned
            TLE_LINE0             varchar(62)
            TLE_LINE1             char(71)
            TLE_LINE2             char(71)
            OBJECT_ID             varchar(11)
            OBJECT_NUMBER         mediumint(8) unsigned
            SEMIMAJOR_AXIS        double(20,3)
            PERIOD                double(20,3)
            APOGEE                double(20,3)
            PERIGEE               double(20,3)
            ===================== =========================



            The following operators can be used with the values

            ========= =======================================================
            Operator  Description
            ========= =======================================================
            >         Greater Than (alternate is %3E)
            <         Less Than (alternate is %3C)
            <>        Not Equal (alternate is %3C%3E)
            ,         Comma Delimited 'OR' (ex. 1,2,3)
            --        Inclusive Range
                      (ex. ``1--100`` returns 1 and 100 and everything in between).
                      Date ranges are expressed as
                      ``YYYY-MM-DD%20HH:MM:SS--YYYY-MM-DD%20HH:MM:SS`` or
                      ``YYYY-MM-DD--YYYY-MM-DD``
            null-val  Value for 'NULL', can only be used with Not Equal (<>) or by itself.
            ~~        "Like" or Wildcard search. You may put the ``~~`` before or
                      after the text; wildcard is evaluated regardless of
                      location of ``~~`` in the URL. For example, ``~~OB`` will return
                      'OBJECT 1', 'GLOBALSTAR', 'PROBA 1', etc.
            ^         Wildcard after value with a minimum of two characters.
                      (alternate is %5E) The wildcard is evaluated after the
                      text regardless of location of ^ in the URL. For example,
                      ``^OB`` will return 'OBJECT 1', 'OBJECT 2', etc. but not 'GLOBALSTAR'
            now       Variable that contains the current system date and time.
                      Add or subtract days (or fractions thereof) after 'now'
                      to modify the date/time, e.g. ``now-7``, ``now+14``, ``now-6.5``,
                      ``now+2.3``. Use <,>,and -- to get a range of dates;
                      e.g. ``>now-7``, ``now-14--now``
            ========= =======================================================

            You can also specify to order results by a specific field by using
            they

            Examples:

            >>> query_tle({'PERIOD': '<128'})
            Satellites currently in Low Earth Orbit (LEO = <2000KM altitude).

            >>> query_tle({'PERIOD':'1430--1450', 'orderby':'NORAD_CAT_ID'})
            Satellites in geosynchronous orbit 1430 <= period <= 1450 minutes.
            Sort results by Norad ID.

        """

        URI = "/basicspacedata/query/class/tle_latest/format/3le/ordinal/1"

        for k,v in list(params.items()):
            URI += "/" + k +"/"+v

        log.debug("Downloading TLE list using URI: %s"%(URI))

        r = requests.get(self.ST_URL+URI, cookies=self.cookies)
        r.raise_for_status()

        return r.content


    def get_tle_sets(self, name):
        """
            A shortcut to some predefined sets of satellites. 
            
            Avaliable sets are:

            ============== ============================================================
            'amateur_all'  space-track.org curated list of amateur radio satellites
            'leo_all'      All satellites in LEO (period < 128 )
            'geo_all'      All satellites in GEO (period between 1430 and 1450)
            ============== ============================================================

            Args:
                name (str): The set to get (see above)

            Returns:
                Concatenated string of TLEs

        """

        if name == "amateur_all":
            l =  self.query_tle({
                'favorites': 'Amateur',
                'EPOCH': '>now-30'})

        elif name == "leo_all":
            l = self.query_tle({
                'PERIOD': '<128'})

        elif name == 'geo_all':
            l = self.query_tle({
                'PERIOD': '1430--1450'})

        else:
            raise Error('Set named %s is not defined'%(name))

        return l
        

    def get_tles(self, nids):
        """
            Query space-track for a series of norad IDs, and return
            the NIDs and TLEs in a dict.

            .. note:: 
                In some cases space-track can not find a TLE. **No error**
                will be raised by this function and it is up to the caller
                to check whether the returned NIDs match the passed ones.

            Args:
                nids (list(int)): List of norad ids to query for

            Returns:
                Python dictionary of NIDS/TLES


        """
        idstr=",".join(str(x) for x in nids)

        tlestr = self.query_tle({'NORAD_CAT_ID':idstr})#.decode()
        if isinstance(tlestr, bytes):
            tlestr = tlestr.decode()
        tlestr = tlestr.strip().replace('\r', '').split('\n')



        L0 = tlestr[0::3]
        L1 = tlestr[1::3]
        L2 = tlestr[2::3]
        tle_list = list(zip(L0,L1,L2))
        nids = [int(x.split(' ')[1]) for x in L2]

        tles = dict(list(zip(nids, tle_list)))

        return tles

class TLEDb(object):
    """
        Database of TLEs.

        The Database can be loaded from a file, or input directly.

        This class can serve as a drop-in replacement for :class:`.SpaceTrackAPI`
        when creating a :class:`.Propagator` as it implements the ``get_tles`` method.

    """

    def __init__(self, fname=None, tles=None):
        """
        .. note::
            Only one of the arguments (fname or tles) must be specified, and not both.

        Args:
            fname (str): The filename to load TLEs from
            tles (dict or str): Manual specificaiton of TLES
        """
        if (fname is not None) and (tles is not None):
            raise Error("only enter fname OR tles")


        if tles is not None:

            if type(tles) is str:
                #parse string

                self.tles = self._parse_tlestr(tles)


            elif type(tles) is dict:
                # load directly
                self.tles = tles



        elif fname is not None:
            # load from file
            fp = open(fname, 'r')
            tlestr = fp.read()
            self.tles = self._parse_tlestr(tlestr)
            fp.close()

        else:
            raise Error("Either a file name or a tle string must be entered")


    def save_tles(self, fname, fformat='txt'):
        """
            Save the database to file.

            Args:
                fname (str): Filename to save to
                fformat (str): Currently has to be 'txt'

        """

        if fformat == 'txt':
            fp = open(fname, 'w')
            tlestr = '\r\n'.join(sum(list(self.tles.values()), ()))
            fp.write(tlestr)
            fp.close()

        elif fformat == 'pickle':
            pass
        else:
            raise Exception('Invalid file format {}'.format(fformat))



    def _parse_tlestr(self, tlestr):

        tlestr = tlestr.strip().replace('\r', '').split('\n')

        L0 = [l.strip() for l in tlestr[0::3]]
        L1 = [l.strip() for l in tlestr[1::3]]
        L2 = [l.strip() for l in tlestr[2::3]]


        # do a tiny bit of error checking and extract nids

        if  all([x[0] == '0' for x in L0]) is False:
            raise Error('Malformed TLE string')

        if  all([x[0] == '1' for x in L1]) is False:
            raise Error('Malformed TLE string')

        if  all([x[0] == '2' for x in L2]) is False:
            raise Error('Malformed TLE string')


        tle_list = list(zip(L0,L1,L2))
        nids = [int(x[2:7]) for x in L2]

        tles = dict(list(zip(nids, tle_list)))

        return tles

    def get_tles(self, nids):
        """
            Query database for a series of norad IDs, and return
            the NIDs and TLEs in a dict.

            .. note:: 
                If the NID is not in the database, **no error**
                will be raised by this function and it is up to the caller
                to check whether the returned NIDs match the passed ones.

            Args:
                nids (list(int)): List of Norad IDs

            Returns:   
                Python dictionary of NIDS/TLES

        """

        tles = dict()
        for n in nids:
            if n in list(self.tles.keys()):
                tles[n] = self.tles[n]

        return tles

class Propagator(object):
    """

    Class to compute pointing angles for a satellite based on its Norad ID

    You can connect to a local Db using the TLEDb class, to spacetrack
    using the SpaceTrackAPI class, or simply just specify the TLEs
    directly as a string. The latter will use the manually input tles and never query space-track.

    For a reference on TLEs see `Wikipedia <https://en.wikipedia.org/wiki/Two-line_element_set>`_

    .. note::
        This class relies heavily on `py-ephem <http://rhodesmill.org/pyephem/>`_

    """

    #: Where to find space-track
    ST_URL="https://www.space-track.org/"

    def __init__(
            self,
            api = None,
            tles = None,
            gs_lat = None,
            gs_lon = None,
            gs_elev = 0,
            tle_timeout=1,
            nids=[]
            ):
        """
        Args:
            api                             : API for TLE updates
            tles (str)                      : TLEstring
            gs_lat (float, optional)        : latitude of ground station
            gs_lon (float, optional)        : longitude of ground station
            gs_elev (float, optional)       : elevation of ground station
            tle_timeout (float, optional)   : Time in days before re-requesting new TLEs
            nids (list(int), optional)      : List of NORAD IDs to track.
                If a satellite is requested that is not in this list it will be
                added and a full refresh of the TLEs from space-track initiated.
        """

        if api is None and tles is None:
            raise Error('You have to specify either uname/pwd or tls')


        if gs_lat is None or gs_lon is None:
            raise Error("gs lon and lat must be specified")

        #: Ground station latitude
        self.gs_lat = gs_lat

        #: Ground station longitude
        self.gs_lon = gs_lon

        #: Ground station elevation
        self.gs_elev = gs_elev


        if tles is not None:
            self._update_tles(tles)

            # big number to avoid tles timing out in manual mode
            self.tle_timeout = 9999999

        else:
            #: List of NIDS to track
            self.nids_to_track = nids

            #: Current TLEs
            self.tles = None

            #: Last requested TLE
            self.tle_timestamp = None

            #: Timeout (in days) before requesting new TLE
            self.tle_timeout = tle_timeout

            #:
            self.api = api

            self._update_tles()



    def _is_visible(self, nid, horizon=0):
        """
            Check if a satellite is above the horizon
        """

        az, el = self.get_angles(nid)

        return (el >= horizon)





    def _update_tles(self, ext_tles=None):#, nids=None):
        """
            Query space-track.org for the trackable tles and save to memory

            Args:
                ext_tles: This argument allows to update the TLEs manually
                    for example for testing. ext_tles should be a string
                    exactly identical in format to what space-track would return
        """
        #if nids is None:
        #    nids = self.nids_to_track

        if ext_tles is None:

            self.tles = self.api.get_tles(self.nids_to_track)
            self.nids_to_track = list(self.tles.keys())


        else:
            raw_tles = ext_tles.replace('\r', '').split('\n')
            raw_tles = [rtle.strip() for rtle in raw_tles]

            # do a tiny bit of error checking and extract nids

            if  all([x[0] == '0' for x in raw_tles[0::3]]) is False:
                raise Error('Malformed TLE string')

            if  all([x[0] == '1' for x in raw_tles[1::3]]) is False:
                raise Error('Malformed TLE string')

            if  all([x[0] == '2' for x in raw_tles[2::3]]) is False:
                raise Error('Malformed TLE string')

            nids = [int(x.split(' ')[1]) for x in  raw_tles[2::3]]
            self.nids_to_track = nids



            #
            # Create a tle dict
            #
            self.tles = {}      #dict to map nid->TLE
            #self.name2nid = {}  #dict to map name->nid
            cnt =  0
            for nid in nids:
                self.tles[nid] = raw_tles[cnt:cnt+3]
                #self.name2nid[self.raw_tles[cnt][2:]] = nid
                cnt += 3

        #
        # Save time for timeout calculation
        #
        self.tle_timestamp = time.time()

    def _tles_have_expired(self):

        if self.tle_timestamp is None:
            return True

        dt = time.time() - self.tle_timestamp

        # Calculate time in days and compare with timeout
        if dt/86400.0 > self.tle_timeout:
            return True
        else:
            return False



    def get_visible_satellites(self, tz='AEST', future_only=True, allow_overlap = True):
        """
            Get a list of current and upcoming radio amateur satellite passes.

            This function gets its data from heavens above. Heavens above does
            not provide an official API and this function therefore scrapes
            the data from the website. It will break without notice if anything changes on
            the heavens above website. That is considered acceptable since
            this function is for information only and does not form any part
            of the core ground station software.

            Args:
                tz (str, optional): The timezone designator, or None for UTC.

        """

        resp = requests.get('http://www.heavens-above.com/AmateurSats.aspx?lat=%f&lng=%f&loc=%s&alt=%.0f%s'%\
            (self.gs_lat, self.gs_lon, 'adfags', self.gs_elev,
             ('' if tz is None else '&tz=%s'%(tz))))

        h = html.document_fromstring(resp.content)
        r = h.xpath('//table[@class="standardTable"]')[0]
        htmlstr = html.tostring(r)
        sats = pd.read_html(htmlstr)[0]
        sats.columns=['Satellite', 'Date', 'Start', 'HP_time', 'HP_Elev', 'HP_Az', 'End', 'Freq']

        sats.HP_Elev = (sats.HP_Elev.str.extract('(\d+)', expand=False)).astype(float)
        sats.HP_Az = (sats.HP_Az.str.extract('(\d+)', expand=False)).astype(float)

        tz = h.xpath('//span[@id="ctl00_lblTZ"]')[0].text_content()

        sats['NID'] = -1
        for index, row in sats.iterrows():
            idx2 = htmlstr.find(row.Satellite)
            idx1 = htmlstr[:idx2].rfind('<a href')
            linkstr = htmlstr[idx1:idx2]
            satid = int(re.findall('satid=(\d+)',linkstr)[0])
            sats.loc[index, 'NID'] = satid

        sats['tz'] = tz


        if future_only:
            # minimum time to wait before first pass starts (in s)
            BUFFER= 60
            sats = sats[sats.Start.apply(pd.to_datetime) > pd.Timestamp.now() + pd.Timedelta(seconds=BUFFER)]

        if not allow_overlap:
            # get rid of overlapping
            no_overl = [True] + [pd.to_datetime(sats.iloc[k].Start) > pd.to_datetime(sats.iloc[k-1].End) for k in range(1, len(sats))]
            sats = sats[no_overl]

        return sats

    def get_tle(self, nid):
        """
        Return TLEs from a NORAD ID by
        quering Space-Track if data is older than the specified timeout
        from memory otherwise

        Args:
            nid (int): Norad ID

        Returns:
            Three line element (TLE)

            If the timeout delay has not been hit it will return the
            most recently fetched TLE, otherwise it will retreive the
            most recent TLE from spacetrack.

        Example:

        >>> A.get_tle(25544)
        ['0 ISS (ZARYA)', '1 25544U 98067A   17164.50922405 +.00002016 +00000-0 +37842-4 0  9993', '2 25544 051.6431 056.6611 0004416 268.2130 149.1141 15.54021074061180']



        """
        if self.tles is None or self._tles_have_expired():
            self._update_tles()


        tles = list(self.tles.keys())
        tles.sort()
        self.nids_to_track.sort()

        if tles != self.nids_to_track:
            raise Error('Unexpected Error')

        if nid not in tles:
            if not hasattr(self, 'api'):
                raise Error('Class has not been connected with an API. Cant request NID')

            self.nids_to_track += [nid]

            self._update_tles()


        return self.tles[nid]


    def get_range(self, nid, gs_lat=None, gs_lon=None, gs_elev=None, when=None):
        return self.get_all(nid, gs_lat, gs_lon, gs_elev, when)['range']

    def get_range_rate(self, nid, gs_lat=None, gs_lon=None, gs_elev=None, when=None):
        return self.get_all(nid, gs_lat, gs_lon, gs_elev, when)['range_rate']

    def get_doppler(self, nid, freq, gs_lat=None, gs_lon=None, gs_elev=None, when=None):
        dv = self.get_range_rate(nid, gs_lat, gs_lon, gs_elev, when)
        return (dv/299792458.0)*freq

    def get_eclipsed(self, nid, gs_lat=None, gs_lon=None, gs_elev=None, when=None):
        return self.get_all(nid, gs_lat, gs_lon, gs_elev, when)['eclipsed']

    def get_angles(self, nid, gs_lat=None, gs_lon=None, gs_elev=None, when=None):
        x =  self.get_all(nid, gs_lat, gs_lon, gs_elev, when)[['az', 'el']]

        if isinstance(x, pd.Series):
            return x.az, x.el
        else:
            return x


    def get_all(self, nid, gs_lat=None, gs_lon=None, gs_elev=None, when=None):
        """
        Just a wrapper around pyephem _compute function, which allows the extraction
        of a  bunch of different parameters through other functions that use
        this one (such as get_angles, get_range, etc...)
        """
        #
        # Allow user to pass gs coordinates, or use stored ones otherwise
        #
        if gs_lat is not None:
            lat = gs_lat
        else:
            lat = self.gs_lat

        if gs_lon is not None:
            lon = gs_lon
        else:
            lon = self.gs_lon

        if gs_elev is not None:
            elev = gs_elev
        else:
            elev = self.gs_elev

        if (lat is None) or (lon is None) or (elev is None):
            raise Error("GS Lat, Lon or Elev have not been specified")

        obs = ephem.Observer()
        obs.lat = str(lat)
        obs.lon = str(lon)
        obs.elevation = elev

        v = ephem.readtle(*self.get_tle(nid))


        if when is None:
            when = [datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S')]
        elif isinstance(when, str):
            when = [when]
        elif not isinstance(when, Iterable):
            when = [when]

        data = DataFrame(index=when, columns= ['norad_id', 'tstamp_str', 'orbit_no', 'az', 'el', 'range', 'range_rate', 'altitude', 'lat', 'long', 'eclipsed'])

        for w in when:
            obs.date = w
            v.compute(obs)
            data.az[w] = v.az/pi*180.0
            data.el[w] = v.alt/pi*180.0
            data.range[w] = v.range
            data.range_rate[w] = v.range_velocity
            data.eclipsed[w] = v.eclipsed
            data.altitude[w] = v.elevation
            data.lat[w] = v.sublat/pi*180.0
            data.long[w] = v.sublong/pi*180.0
            data.tstamp_str[w] = str(w)
            data.norad_id[w] = nid
            data.orbit_no[w] = self._calculate_orbit_no(nid, w)

        if pd.isnull(data).any().any():
            raise Error('Unexpected error: dataframe has not filled as expected')


        data.index.name='tstamp'

        # This is not a nice way to store attributes since it does not persist
        # if we do something to the dataframe, so in this funciton it is also
        # saved as a column (also not very nice). Anyway, the below is relied
        # on for several functions so dont remove.
        data.nid = nid
        
        # For convenience we also store the TLE this way. It is not relied on
        # but if it is not set then the TLE will not end up in the libgs log
        # (unless manually added as metadata to CommsPass under the TLE key)
        data.TLE = '\n'.join(self.get_tle(nid))

        if len(data) == 1:
            return(data.iloc[0])
        else:
            return data



    def get_angles_old(self, nid, gs_lat=None, gs_lon=None, gs_elev=None, when=None):
        """
          If the user prefers to calculate the angles at a specific time he
          should set when=YYYY/MM/DD HH:mm:ss. when can also be an array

        """
        #
        # Allow user to pass gs coordinates, or use stored ones otherwise
        #
        if gs_lat is not None:
            lat = gs_lat
        else:
            lat = self.gs_lat

        if gs_lon is not None:
            lon = gs_lon
        else:
            lon = self.gs_lon

        if gs_elev is not None:
            elev = gs_elev
        else:
            elev = self.gs_elev

        if (lat is None) or (lon is None) or (elev is None):
            raise Error("GS Lat, Lon or Elev have not been specified")

        obs = ephem.Observer()
        obs.lat = str(lat)
        obs.lon = str(lon)
        obs.elevation = elev

        v = ephem.readtle(*self.get_tle(nid))


        if when is None:
            obs.date = datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S')
        elif type(when) is not list:
            obs.date = when

        if type(when) is list:
            pos = DataFrame(index=when, columns= ['tstamp_str', 'az', 'el'])

            for w in when:
                obs.date = w
                v.compute(obs)
                pos.az[w] = v.az/pi*180.0
                pos.el[w] = v.alt/pi*180.0
                pos.tstamp_str[w] = str(w)

            if pd.isnull(pos).any().any():
                raise Error('Unexpected error: dataframe has not filled as expected')


            pos.nid = nid
            return pos



        else:
            v.compute(obs)

            #
            # Return Azimuth, Elevation (in deg)
            #
            return v.az/pi*180.0, v.alt/pi*180.0


    def get_ground_coord(self, nid, when=None):
        """
          Return the ground track lat/long coord without needing the ground station
          coordinates
        """

        obs = ephem.Observer()

        if when is None:
            obs.date = datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S')
        else:
            obs.date = when

        v = ephem.readtle(*self.get_tle(nid))
        v.compute(obs)
        return v.sublat/pi*180.0, v.sublong/pi*180.0

    # TODO: Add eclipsed and get_ground_coord and get_orbit to extend a base
    # function taht doesnt depend on gs lat/lon (in same way as get_all above)

    def get_orbit(self, nid, when=None):
        """
            Return the orbital elements
        """
        obs = ephem.Observer()

        if when is None:
            obs.date = datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S')
        else:
            obs.date = when

        v = ephem.readtle(*self.get_tle(nid))
        v.compute(obs)


        data = {\
        'epoch' : v._epoch,
        'e'     : v._e,
        'inc'   : v._inc/pi*180.0,
        'raan'  : v._raan/pi*180.0,
        'ap'    : v._ap/pi*180.0,
        'n'     : v._n,
        'M'     : v._M/pi*180.0,
        'orbit' : v._orbit}

        return data

    def _get_observer(self, gs_lat=None, gs_lon = None, gs_elev = None, when=None):

        #
        # Allow user to pass gs coordinates, or use stored ones otherwise
        #
        if gs_lat is not None:
            lat = gs_lat
        else:
            lat = self.gs_lat

        if gs_lon is not None:
            lon = gs_lon
        else:
            lon = self.gs_lon

        if gs_elev is not None:
            elev = gs_elev
        else:
            elev = self.gs_elev



        if (lat is None) or (lon is None) or (elev is None):
            raise Error("GS Lat, Lon or Elev have not been specified")

        obs = ephem.Observer()
        obs.lat = lat/180.0*pi
        obs.lon = lon/180.0*pi
        obs.elevation = elev

        if when is None:
            obs.date = datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S')
        # elif isinstance(when, str):  #<-- this does not work for py3, but may be necessary for py2 ... TODO
        #     obs.date = when.encode()
        else:
            obs.date = when

        return obs

    def get_passes(self, nid=None, N=1, when=None, horizon=0):
        """
            Compute the next passes

            Args:
                nid (int, optional): compute the next pass for a given nid.
                    If nid is omitted, compute the next pass for all tracked
                    satellites.

                hor (float, optional): horizon angle
        """

        passes = []
        if nid is None:
            iterable = self.nids_to_track
        elif type(nid) is list:
            iterable = nid
        elif type(nid) is int:
            iterable = [nid]
        else:
            raise Error('nid is malformed')

        # Check if satellite is currently visible without having to call
        #  get_angles. Just do two next_pass calculations: one for now, one
        #  for 10 minutes ago. Check that they match. If not use the one from
        #
        # if yes: either delay time enough to get next pass later
        #         or advance time to include this pass... tbd

        for nid in iterable:

            #print(nid)

            i = 0
            nextwhen = when
            while i < N:
                obs = self._get_observer(when=nextwhen)
                soon_date = ephem.Date(obs.date + (1.0/86400))

                tle = ephem.readtle(*self.get_tle(nid))

                try:
                    p = obs.next_pass(tle)
                except Exception as e:
                    log.warning("Trying to get pass for NID %d, but cant: %s"%(nid, e))
                    i += 1
                    continue

                if not any(p[2:]):
                    log.warning("Trying to get pass for NID %d, but cant. It may no longer be in orbit"%(nid))
                    i+=1
                    continue


                if not (p[0]< p[4]):
                    # satellite is probably currently visible

                        # compute pos in 1 sec and set as rising
                        az,el = self.get_angles(nid, when=soon_date)

                        if soon_date <= p[2]:
                            p = (soon_date, el/180.0*pi, p[2], p[3], p[4], p[5])

                            # if maximum has also been passed, set it to be the same
                        elif soon_date > p[2]:
                            p = (soon_date, el/180.0*pi, soon_date, az/180.0*pi, p[4], p[5])

                        else:
                            raise Error('Unexpected')

                nextwhen = ephem.Date(p[4] + 60.0/86400)


                # convert to a str format that
                # a) parses with pd.to_datetime
                # b) parses with ephem.Date
                # c) sorts correctly
                dstr = lambda x : x.datetime().strftime('%Y/%m/%d %H:%M:%S')

                if p[3]/pi*180.0 < horizon:
                    continue
                else:

                    passes += [(nid, self._calculate_orbit_no(nid, str(p[0])),
                    dstr(p[0]),  p[1]/pi*180.0,
                    dstr(p[2]),  p[3]/pi*180.0,
                    dstr(p[4]),  p[5]/pi*180.0)]
                    i += 1


        passes = DataFrame(passes, columns = ['nid', 'orbit_no',  'rise_t', 'rise_az', 'max_elev_t', 'max_elev', 'set_t', 'set_az'])

        if len(passes) > 1:
            passes = passes.sort_values(by='rise_t').reset_index(drop=True)
            passes.index.name="pass_no"
        if len(passes) == 1:
            passes.index.name = "pass_no"
            passes = passes.iloc[0]
        elif len(passes) < 1:
            raise Error('An unexpected error occurred when computing passes')

        return passes



    def compute_pass(self, nid, key_els = [], when=None, dt=1.0):
        """
            Perform a detailed calculation of the pass and
            return the trajectory in a dataframe

            Also compute the keypoints for which the trajectory passes through
            a set of elevations (specified)

            Args:
                key_els (list(float), optional): list of elevations to compute
                keypoints for. elevations less than 1 deg apart are ignored.
        """


        # get upcoming pass
        p = self.get_passes(nid, when=when)
        ta = _tstamp_array(p.rise_t, p.set_t, dt=dt)

        if len(ta) < 3:
            raise Error('pass is too short to compute')


        angs = self.get_all(nid, when=ta)

        p_max = angs[angs.el == angs.el.max()].iloc[0]
        p_rise = angs[angs.el > 0].iloc[0]
        p_set  = angs[angs.el > 0].iloc[-1]

        if  len(key_els) > 0:
            key_els.sort()
            key_els = np.unique([int(k) for k in key_els])

            keypoints = [None] * len(key_els) * 2

            i = 0
            for el in key_els:
                if (angs.el > el).any() == False:
                    raise Error('Pass never reaches requested keypoint elevation')

                keypoints[i] = angs[angs.el > el].iloc[0]
                keypoints[-1-i] = angs[angs.el > el].iloc[-1]
                i += 1


            keypoints = [p_rise] + keypoints[:len(key_els)] + [p_max] + keypoints[len(key_els):] + [p_set]

        else:
            keypoints= [p_rise, p_max, p_set]


        kpoints = DataFrame(keypoints)
        kpoints.index = ['rise'] + ['rise%02d'%(d) for d in key_els] + ['peak'] + ['set%02d'%(d) for d in key_els[::-1]] + ['set']
        return angs, kpoints

    def _calculate_orbit_no(self, NID, when):
        orbit = self.get_orbit(NID, when=when)
        ep = orbit['epoch'] # time at TLE epoch
        n  = orbit['n'] # mean motion (rev/day)
        orb_e = orbit['orbit'] # orbit no at epoch
        M   = orbit['M'] # mean anomaly at epoch ("angle" of epoch)
        ap = orbit['ap'] # argument of perigee (angle of perigee)
        t = ephem.Date(when)
        ep_an = ep - (1.0/n) * (M + ap)/360.0 #time of last ascending node

        return orb_e + n*(t - ep_an)


    def print_info(self, nid, when=None):
        """
        Print all info about a specific space item

        Args:
        nid: Norad ID of object

        """

        if when is None:
            tstamp = datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S')
        else:
            tstamp = when


        tle = self.get_tle(nid)
        #lat,lon = self.get_ground_coord(nid, when=tstamp)
        #az,el = self.get_angles(nid, when=tstamp)
        sdata = self.get_all(nid, when=tstamp)

        _print("TLE (updated %s):"%(datetime.fromtimestamp(self.tle_timestamp).strftime('%d/%m/%Y %H:%M:%S')))
        _print("\n    ".join(tle))

        odata = self.get_orbit(nid)
        _print("\nOrbit:")
        _print("        epoch (utc) : %s"%(odata['epoch']))
        _print("        eccentricity: %f"%(odata['e']))
        _print("        inclindation: %f"%(odata['inc']))
        _print("                RAAN: %f"%(odata['raan']))
        _print("                  AP: %f"%(odata['ap']))
        _print("       revol per day: %f"%(odata['n']))
        _print("  mean anom at epoch: %f"%(odata['M']))
        _print("   orbit no at epoch: %d"%(odata['orbit']))

        _print("\nObserver:")
        _print("                 lat: %f\n                 lon: %f\n                elev: %.0f\n          date (utc): %s"%(
            self.gs_lat, self.gs_lon, self.gs_elev, tstamp))

        _print("\nSatellite:")
        _print("    ground track pos: (lat = %.3f, lon = %.3f)"%(sdata['lat'],sdata['long']))
        _print("            pointing: (az  = %.3f, el  = %.3f)"%(sdata['az'],sdata['el']))
        _print("               range: %f"%(sdata['range']))
        _print("          range rate: %f"%(sdata['range_rate']))
        _print("            altitude: %f"%(sdata['altitude']))
        _print("        orbit number: %f"%(sdata['orbit_no']))

if __name__ == '__main__':
    pass