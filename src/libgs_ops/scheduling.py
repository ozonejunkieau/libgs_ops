# -*- coding: utf-8 -*-
"""
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


Created on Sun Aug  6 17:36:19 2017

@author: kjetil
"""

import pandas as pd
from pandas import DataFrame
import numpy as np
import json
import ephem
import os
from rpc import RPCClient
import logging
log = logging.getLogger('libgs_ops-log')
log.addHandler(logging.NullHandler())


##########
#Extract from utils
###
def bytes2hex(data):
    data =bytearray(data)
    return('-'.join(["%02X"%(x) for x in data]))


def hex2bytes(hexstr):
    data = hexstr.split('-')
    return bytearray(''.join([chr(int(x, 16)) for x in data]))

class Error(Exception):
    pass

SCHEDULE_BUFFERTIME = 180

############


class Action(dict):
    """
    Actions are just a list and/or dict
    of parameters that will be passed unmodified to the protocol.

    It can be useful if issuing non-standard commands (ie not bytearrays)
    to the protocol class for whatever reason.
    """

    def __init__(self, args, kwargs={}, desc = "unnamed",  retries=0):

        if isinstance(args, list):
            args = tuple(args)

        if not isinstance(args, tuple):
            raise Error('args must be a tuple, not %s'%(type(args)))
        if not isinstance(kwargs, dict):
            raise Error('kwargs must be a dict, not %s'%(type(args)))

        self['desc'] = desc
        self['args'] = args
        self['kwargs'] = kwargs

        # Make something persist through the pass by setting retries to be
        # realy large, and allow the user to say retries=-1 for convenience.
        if retries < 0:
            retries =  10000000

        self['retries'] = int(retries)


        try:
            json.dumps(self)
        except TypeError as e:
            raise Error("All arguments to Action have to be json-serializable objects. Refer to python documentation (%s)", e)

    def __str__(self):
        return("Action: %s <%s, %s> (%d retries)"%(self['desc'], self['args'], self['kwargs'], self['retries']))

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return dict(self)

class Communication(dict):
    """
    This class holds the message (fully encoded) that is sent to the
    satellite.

    It is just a convenience class that wraps and populates a dictionary
    properly for use by the other classes in this module.


    """

    def __init__(self,cmd, retries=3, wait = True):
        """

        Args:
            cmd (string or bytearray): Command string (fully encoded) to send
            to satellite.
            retries (int): Number of times the command should be retried in
            case of failure
            wait (bool): Whether the ground station should wait for a reply
            from the satellite or not.

        """

        if isinstance(cmd, basestring):
            self._check_cmdstr(cmd)
            barray = hex2bytes(cmd)
            hexstr = cmd
        elif isinstance(cmd, bytearray):
            hexstr = bytes2hex(cmd)
            barray = cmd
        elif isinstance(cmd, Communication):
            hexstr = cmd['hexstr']
            barray = cmd['barray']
        else:
            raise Error('Unsupported argument : %s -  %s'%(cmd, type(cmd)))


        if type(retries) != int or retries < 0:
            raise Error("Retries must be an integer > 0")

        self['barray'] = barray
        self['hexstr'] = hexstr
        self['retries'] = retries
        self['wait'] = wait


    def _check_cmdstr(self, cmd):
        """
        Verify that the command string is in the right format

        """
        valid = '0123456789ABCDEF-'

        # do some input checking
        # cmd must be in format XX-XX-XX-XX
        #
        if not (np.array([len(s) for s in cmd.split('-')])  == 2).all():
            raise Error("cmd srting must be in the format XX-XX-XX-XX")

        if not (np.array([a in valid for a in cmd]).all()):
            raise Error("cmd string invalid hex")


    def to_dict(self):
        # Turn to serialisable dict... we get rid of bytearray entry.
        c = dict(hexstr=self['hexstr'], retries=self['retries'], wait=self['wait'])
        return c




class CommsPass(object):
    """
    Class to hold a communications pass

    """

    _metadata = None

    def __init__(self, pass_data, desc=None, nid=None, horizon=0, comms=[], listen=False, **kwargs):
        """
        Args;
            pass_data (): Pandas DataFrame with at least az, el, range_rate columns
            nid (int)   : Norad ID to associate with pass. Can be left empty if pass_data has a .nid field.
            horizon (float): The lowest acceptable elevation for the pass. Pass_data will be cropped to the horizon
            comms (list, optional) : List of communications (can be added with add_communications instead)
            listen (bool, optional): Whether it is a listen pass or not
            tle (str, optional)    : The TLE used for computing pass_data
            protocol (str, optional): The protocol to use during the pass
            **kwargs: Any other key=value pair to pass to scheduler to be logged

        """
        # NOTE: Internally, picklable arguments (i.e. everything except pass_data and comms) are
        #       stored in metadata dictionary so it can be easily converted
        #       to dict/json, regardless of what is being passed.

        #initialising _metadata attribute is a bit tricky since we have overloaded __setattr__
        object.__setattr__(self, '_metadata', {})

        if not ('az' in pass_data.keys() and 'el'in pass_data.keys() and 'range_rate' in pass_data.keys() and 'tstamp_str'in pass_data.keys()):
            #print(pass_data.head())
            raise Error('Pass_data must be a dataframe with at least "az", "el", "range_rate" and "tstamp_str" columns')

        # Initiate named metadata fields) - afterwareds we can access with . operator
        self.metadata['nid'] = None #<--- initialise metadata - will then be set correctly with .nid access immediately below
        self.metadata['listen'] = listen
        self.metadata['horizon'] = horizon
        self.metadata['desc'] =  desc
        
        if hasattr(pass_data, 'TLE') and 'tle' not in kwargs.keys():
            self.metadata['tle'] = pass_data.TLE


        #
        # Check NID
        #
        if nid is None:
            if hasattr(pass_data, 'nid'):

                if 'norad_id' in pass_data.keys():
                    pd_nid = pass_data.norad_id.unique()
                    if (len(pd_nid) != 1) or (pd_nid[0] != pass_data.nid):
                        raise Error("nid is set as an attribute on pass_data and also as a norad_id column, but there is a mismatch")

                self.nid=pass_data.nid

            elif 'norad_id' in pass_data.keys():
                pd_nid = pass_data.norad_id.unique()
                if len(pd_nid) != 1:
                    raise Error("norad_id column is available in pass_data, but not unique - it should be")

                self.nid = pd_nid[0]
            else:
                raise Error("Norad ID (nid) is needed, but is not available in pass data or passed as an argument")
        else:
            self.nid = nid



        #
        # Check timestamp
        #
        try:
            tstamps = [ephem.Date(pd.to_datetime(s)) for s in pass_data.tstamp_str]
        except Exception as e:
            raise Error("Badly formatted date(s) in pass_data.tstamp_str: %s"%(e))

        pass_data.index = tstamps
        pass_data.tstamp_str = [str(s) for s in tstamps]

        # Crop data to only contain waht is above the horizon
        pass_data = pass_data[pass_data.el >= self.horizon]

        if pass_data.empty:
            raise Error('Pass never comes above visibility horizon')

        # While strictly not necessay, not curating what gets stored in the commspass
        # makes it difficult to do automated testing. So this will need to be edited
        # if in the future we need anything more
        pass_data = pass_data[['tstamp_str', 'az', 'el', 'range_rate']]

        self.pass_data = pass_data
        self.comms = []

        for comm in comms:
            self.add_communication(comm)

        # Add any additional metadata fields
        self.metadata.update(kwargs)





    def _change_time(self, tstamp):
        """
        Debugging function: Adjusts the timestamp as required
        If you run this it will not correspond to a real satellite anymore

        """
        curt =  self.pass_data.index[0]
        newt = ephem.Date(tstamp)

        dt = (newt-curt)
        newindex = pd.Series(self.pass_data.index + dt)


        s = newindex.apply(lambda x: str(ephem.Date(x))).tolist()


        new_pass_data = DataFrame(\
            index=self.pass_data.index + dt,
            data = dict(
                tstamp_str = s,
                az = self.pass_data.az.tolist(),
                el = self.pass_data.el.tolist(),
                range_rate = self.pass_data.range_rate.tolist()))

        self.pass_data = new_pass_data






    def __str__(self):
        s = "Communication Pass:\n"
        s += "  Norad ID:       %s\n"%(self.nid)
        s += "  Description:    %s\n"%(self.desc)
        s += "  Visib. horizon: %d\n"%(self.horizon)
        s += "  Pass start:     %s\n"%(self.pass_data.tstamp_str.iloc[0])
        s += "  Pass end:       %s\n"%(self.pass_data.tstamp_str.iloc[-1])
#        for k,v in self._metadata.items():
#            s += "  {:16s}{:s}\n".format(str(k),str(v))

        s += "  Scheduled comms:\n"

        if self.listen:
            s += "   (listen mode)\n"
        elif len(self.comms) == 0:
            s += "   (no comms added but NOT listen mode)"

        for k,v in enumerate(self.comms):

            if v['retries'] > 99:
                retrstr = '(%10s)'%(v['retries'])
            else:
                retrstr = '(%2d retries)'%(v['retries'])


            if isinstance(v, Action):
                s += "   %3d %s : '%s' <%s, %s>\n"%(k, retrstr, v['desc'],  v['args'], v['kwargs'])
            else:
                if v['wait']:
                    s += ("   %3d %s : %s\n"%(k, retrstr,v['hexstr']))
                else:
                    s += ("   %3d (no wait)    : %s\n"%(k, v['hexstr']))

        return(s)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        """

        x == y should be true if everything is identical

        """

        try:
            eq = [\
                self.nid == other.nid,
                self.desc == other.desc,
                (self.pass_data == other.pass_data).all().all(),
                self.horizon == other.horizon,
                self.comms == other.comms,
                self._metadata == other._metadata]
        except ValueError:
            return False

        return all(eq)

    def overlaps(self, other, buffertime=0.0):
        """
        Check if current pass overlaps with another pass.

        By overlap is meant that the other pass begins within a
        defined buffertime of the current pass finishing.

        Args:
            other (CommsPass): The pass to compare with
            buffertime (float): The time in seconds to allow as a minimum between passes

        """
        rt0 = pd.to_datetime(self.pass_data.iloc[0].tstamp_str)
        st0 = pd.to_datetime(self.pass_data.iloc[-1].tstamp_str)
        rt1 = pd.to_datetime(other.pass_data.iloc[0].tstamp_str)
        st1 = pd.to_datetime(other.pass_data.iloc[-1].tstamp_str)

        btime = pd.Timedelta(seconds = buffertime)

        if (   ((rt0 < rt1) and ((st0 + btime) < rt1))
            or ((rt1 < rt0) and ((st1 + btime) < rt0))):
                return False
        else:
            return True

    def __cmp__(self,other):
        return cmp(self.pass_data.index[0],other.pass_data.index[0])



#    def get_metadata(self, key):
#        return self._metadata[key]
#
#    def set_metadata(self, key, val):
#        self._metadata[key] = val

    @property
    def metadata(self):
        return self._metadata


    def __getattr__(self, key):
        """
        Make it possible to access metadata directly through . operator
        """
        try:
            return self.metadata[key]
        except KeyError:
            raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, key))

    def __setattr__(self, key, val):
        """
        Make it possible to access metadata directly through . operator
        """
        if key in self.metadata.keys():
            self.metadata[key] = val
        else:
            object.__setattr__(self, key, val)


    #
    # Add some helper methods to make the class pickle-able
    # It doesnt work out of the box because of our fiddling with __getattr__ and __setattr__
    # So we will make it use by keeping the state as the dict version instead.
    #
    def __getstate__(self):
        return self.to_dict()

    def __setstate__(self, state):
        object.__setattr__(self, '_metadata', {})
        cp = CommsPass.from_dict(state)
        self._metadata = cp._metadata
        self.pass_data = cp.pass_data
        self.comms     = cp.comms
    ########################################################



    def add_communication(self, comm, **kwargs):#comm, retries=3, wait=True):
        """
            Add a communication to the pass. The communication can be supplied
            either as a string of HEX-pairs, as a bytearray, or as a Communications
            object.

            If a HEX string or a bytearray is supplied, it will be converted to a
            Communication object internally

        """

        if isinstance(comm, Communication):
            if len(kwargs) > 0:
                raise Error("No kwargs expected for Communication object, got %s"%(kwargs))

            self.comms.append(comm)

        elif isinstance(comm, Action):
            if len(kwargs) > 0:
                raise Error("No kwargs expected for Action object, got %s"%(kwargs))

            self.comms.append(comm)


        elif isinstance(comm, basestring) or isinstance(comm, bytearray):

            if 'retries' in kwargs.keys():
                retries = kwargs['retries']
            else:
                retries = 3


            if 'wait' in kwargs.keys():
                wait = kwargs['wait']
            else:
                wait = True

            self.comms.append(Communication(comm, retries, wait))
        else:
            raise Error("Invalid type for comms object: %s"%(type(comm)))



        if self.listen:
            log.info("Cannot use listen mode when communicating. listen mode disabled")
            self.listen = False


    def plot(self):
        """
        Visualise the pass
        """
        raise Error("Not implemented")


    def to_dict(self):

        d = dict(
            pass_data = self.pass_data.to_dict(),
            comms = [c.to_dict() for c in self.comms],
            _metadata = self._metadata)

        return (d)

    def copy(self):
        return(CommsPass.from_dict(self.to_dict()))

    @classmethod
    def from_dict(self, d):
        """
        Create CommsPass object from a python dict

        Arg:
            d (dict): dictionary

        """

        pass_data = DataFrame(d['pass_data'], columns = ['tstamp_str', 'az', 'el', 'range_rate'])
        pass_data.index = pass_data.index.astype(float)
        comms = d['comms']

        #################################
        # Allow backwards compatability
        # TODO: Remote and replace with just:
        # _metadata = d['_metadata']
        #
        _metadata = d.copy()
        del _metadata['comms']
        del _metadata['pass_data']

        if '_metadata' in d.keys():
            del _metadata['_metadata']
            _metadata.update(d['_metadata'])
        #################################


        cpass = CommsPass(pass_data, **_metadata)
        for k,c in enumerate(comms):
            if 'args' in c.keys() and 'kwargs' in c.keys() and 'desc' in c.keys() and 'retries' in c.keys():
                cpass.add_communication(Action(c['args'], c['kwargs'], retries=c['retries'], desc=c['desc']))
            elif 'hexstr' in c.keys() and 'retries' in c.keys() and 'wait'in c.keys():
                cpass.add_communication(c['hexstr'], retries=c['retries'], wait=c['wait'])
            else:
                raise Error("Invalid dict input to from_dict. Expected either Action or Communication in dict form, got %s"%(c))

        return cpass

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_json(self, data):
        """
        Create CommsPass from a json string or from a json file.

        Arg:
            json (fname or string): json string or file to load
        """

        if os.path.isfile(data):
            fp = open(data, 'r')
            data = fp.read()
            fp.close()

        d = json.loads(data)

        return self.from_dict(d)



class Schedule(object):

    def __init__(self, passes=[], buffertime = SCHEDULE_BUFFERTIME):
        """
            Create a schedule of communication passes.

            Args:
                passes (list(CommsPass)): List of CommsPass objects
                buffertime (int, optional) : number of seconds to allow, as a minimum
                    between two passes
        """

        #
        # sorting can be disabled, but there is no obvious reason
        # why you would do that. It may also not be safe
        #
        self.sort_passes = True
        self.buffertime = buffertime

        self.passes = []
        for p in passes:
            self.add_pass(p)


    def __str__(self):
        s =  'Schedule of communication passes:\n'
        s += '  ---- -------- -------------------- -------------------- --------------\n'
        s += '  #    Norad id Pass start (utc)     Pass end (utc)       Communications\n'
        s += '  ---- -------- -------------------- -------------------- --------------\n'
        i = 0
        for p in self.passes:
            s += '  %04d %-8s %-20s %-20s %d\n'%(
                i,
                str(p.nid),
                p.pass_data.tstamp_str.iloc[0],
                p.pass_data.tstamp_str.iloc[-1],
                len(p.comms))
            i += 1
        s += '  ---- -------- -------------------- -------------------- --------------\n'
        return(s)

    def __repr__(self):
        return self.__str__()

    def _repr_html_(self):
        rows = []
        for p in self.passes:
            rows += [(p.nid, p.pass_data.tstamp_str.iloc[0], p.pass_data.tstamp_str.iloc[-1], len(p.comms))]

        df = DataFrame(\
            rows,
            columns=['Norad id', 'Pass start (utc)', 'Pass end (utc)', 'Communications'])

        return df._repr_html_()


    def __eq__(self, other):
        """

        x == y should be true if everything is identical

        """
        return (self.__dict__ == other.__dict__)


    def copy(self):
        return(Schedule.from_dict(self.to_dict()))


    def add_pass(self, tpass):

        # check for overlap. Raises exception if overlap
        self._check_overlap(tpass)

        #if all good, add
        self.passes.append(tpass)

        if self.sort_passes == True:
            self.passes.sort(key=lambda p : p.pass_data.index[0])

    def remove_pass(self, tpass):
        self.passes.remove(tpass)

    def pop_pass(self, index=[]):
        self.passes.pop(index)

    def _check_overlap(self, tpass):

        if any([tpass.overlaps(x, buffertime=self.buffertime) for x in self.passes]):
            raise Error("Can't add pass as it overlaps with another pass in the schedule")


    def to_dict(self):
        d = dict(
            passes = [p.to_dict() for p in self.passes],
            sort_passes = self.sort_passes,
            buffertime = self.buffertime)

        return(d)

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


    @classmethod
    def from_dict(self, d):
        """
        Create Schedule object from a python dict

        Arg:
            d (dict): dictionary

        """
        passes = [CommsPass.from_dict(x) for x in d['passes']]
        s = Schedule(passes, d['buffertime'])
        s.sort_passes = d['sort_passes']
        return(s)

    @classmethod
    def from_json(self, data):
        """
        Create Schedule from a json string or from a json file.

        Arg:
            json (fname or string): json string or file to load
        """

        if os.path.isfile(data):
            fp = open(data, 'r')
            data = fp.read()
            fp.close()

        d = json.loads(data)

        return self.from_dict(d)



class RPCSchedulerClient(object):
    """
    The RPCSchedulerClient class can replace the scheduler class in remote
    operations. It connects to the RPCSchedulerClient on the ground station
    for easy communication and execution of schedules.

    """

    def __init__(self, schedule, track_full_pass=False, compute_ant_points = True, rpcaddr='http://localhost:8000'):
        self._rpcaddr =  rpcaddr
        self._track_full_pass = track_full_pass
        self._compute_ant_points = compute_ant_points
        self.server = RPCClient(self._rpcaddr, allow_none=True)
        self._schedule = schedule

    @property
    def state(self):
        return self.server.scheduler_state()


    def execute(self, N=None):
        self.server.execute_schedule(self._schedule.to_json(), self._track_full_pass, self._compute_ant_points, N)

    def stop(self):
        self.server.stop_schedule()



if __name__ == '__main__':

    if 1:
        import sys
        log.setLevel(logging.INFO)

        ch = logging.StreamHandler(sys.stdout)
        #
        # Attributes can be found here: https://docs.python.org/2/library/logging.html#logrecord-attributes
        #
        formatter = logging.Formatter('%(asctime)s - %(levelname)5s - %(module)10s - "%(message)s"')

        # add formatter to ch
        ch.setFormatter(formatter)

        # add ch to logger
        log.addHandler(ch)


