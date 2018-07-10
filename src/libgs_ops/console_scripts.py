from __future__ import print_function
import sys
import argparse
import pandas as pd
from StringIO import StringIO
from propagator import SpaceTrackAPI, Propagator
from scheduling import CommsPass, Communication, Action, Schedule


def _print(*args, **kwargs):
    print(*args,file=sys.stderr, **kwargs)
    
def _fix_timestamp(when):
    if not isinstance(when, basestring):
        raise Exception("_fix_timestamp requires a string")
    return pd.to_datetime(when).strftime("%Y/%m/%d %H:%M:%S")
    
def _rev_timestamp(when):    
    if not isinstance(when, basestring):
        raise Exception("_rev_timestamp requires a string")
    return pd.to_datetime(when).strftime("%Y-%m-%dT%H:%M:%SZ")

def download_tle():
    
    parser = argparse.ArgumentParser(description='Download TLE(s) from space-track.org')
    parser.add_argument("user", help='Space-track.org username')
    parser.add_argument("password", help='Space-track.org password')
    parser.add_argument("-s", "--set", choices=['amateur_all', 'leo_all', 'geo_all'], help="Get TLE set.")
    parser.add_argument("-q", "--query-tle", type=str, help="Perform a fairly raw query for a tle against the space-track api.")
    parser.add_argument("nid", nargs='*', help='Norad ID to download (optional if -s or -q provided)')    
    args = parser.parse_args()
        
    try:
        api = SpaceTrackAPI(args.user, args.password)
    except Exception as e:
        _print("ERROR: Could not connect to space-track. Message ({}): {}".format(e.__class__.__name__, e))
        exit(1)
    
    if args.set is not None:
        tles = api.get_tle_sets(args.set.lower())
    elif args.query_tle is not None:
        tles = api.query_tle(args.query_tle)
    elif len(args.nid) > 0:
        tles = api.get_tles(args.nid)
        tles = "\n".join(["\n".join(v) for v in tles.values()])
    else:
        _print("ERROR: Either -s, or -q or Norad IDs must be specified")
        exit(1)
        
    print(tles)
    exit(0)


def propagate():
    
    action_help="""
    
    Actions
    ========
     info     : print all info about the spacecraft
     get_all  : get all data and return as a csv
     get_pass : quickly find upcoming pass(es)
     compute  : compute pass details
    
    Ground station specification
    ============================
     The ground station can be specified with the --gslat, --gslon, --gselev params,
     or alternatively by a simple text file with those three fields separated by comma.
     The file should either be called gs.txt or specified with --gs.
     
    
    Examples
    ========
    
    $ libgs-propagate info
      Print info about current state of spacecraft described by TLE. Get TLE from stdin
       
    $ libgs-propagate -i tles.txt -w "2018-01-01 10:00" "2018-01-01 10:05" "2018-01-01 10:10" get_all
      Compute everything we can about the tles at the times specified and return a CSV
      
    $ libgs-propagate -i tles.txt -N 10 get_pass
      Get overview of next 10 passes and return a CSV
    
    $ libgs-propagate -i tles.txt --nid 25440 compute 
      Compute upcoming pass for TLE 25440 and return a CSV with same fields as get_all
    
    """
    
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='Propagate a TLE', epilog = action_help)
    parser.add_argument("-i", "--input", help="Input file with TLE(s). Omit to get TLE(s) from stdin")
    parser.add_argument("-n", "--nid", type=int, nargs="*", help="Norad ID(s) of TLE(s) to propagate. If omitted does all provided TLEs")
    parser.add_argument("-w", "--when", type=str, nargs="*", help="Timestamps at which to propegate. Default=now")
    parser.add_argument("--gslat", type=float, help="Ground station latitiude (overrides --gs)")
    parser.add_argument("--gslon", type=float, help="Ground station longitude (overrides --gs)")
    parser.add_argument("--gselev", type=float, help="Ground station elevation (overrides --gs)")
    parser.add_argument("-g", "--gs", type=str, default="gs.txt", help="Ground station specification file (use instead of gslat/lon/elev)")
    parser.add_argument("-H", "--horizon", type=float, default=5, help="Visibility  horizon")
    parser.add_argument("-N", type=int, default=1,help="(Only with get_pass action) Number of passes to get")
    parser.add_argument("--dt", type=int, help = "(Only with compute action) Time interval to compute data at")
    parser.add_argument("action", choices = ["info", "get_all", "get_pass", "compute"], help="Action to take")
    parser.add_argument("-p", "--print", action="store_true", help="Pretty print output")
    parser.add_argument("-f", "--field", nargs="+", help="Filter output by one or more fields")
    parser.add_argument("--no-header", action="store_true", help="Dont output csv header")
    args = parser.parse_args()

    if args.input is not None:
        try:
            with open(args.input, "r") as fp:
                tles = fp.read()
        except Exception as e:
            _print("ERROR: Could not read file {}".format(args.input))
            exit(1)
    else:
        _print("Enter TLE(s). EOF (Ctrl-D) to finish")
        tles = sys.stdin.read()
    tles = tles.strip()

    
        
    if (args.gslat is not None and args.gslon is not None and args.gselev is not None):
        pass
    elif args.gs is not None:
        try:
            with open(args.gs, "r") as fp:
                gslat, gslon, gselev = [float(x) for x in fp.read().split(',')]
        except Exception as e:
            _print("ERROR: Could not parse groundstation definition file. Message ({}): {}".format(e.__class__.__name__, e))          
            exit(1)
    else:
        _print("ERROR: Ground station location needs to be defined (either with --gslat/--gslon/--gselev or wiht --gs file)")
        exit(1)
        
    if args.gslat is not None:
        gslat = args.gslat
    
    if args.gslon is not None:
        gslon = args.gslon
        
    if args.gselev is not None:
        gselev = args.gselev
        
    try:
        p = Propagator(tles=tles, gs_lat = gslat, gs_lon = gslon, gs_elev=gselev)
    except Exception as e:
        _print("ERROR: Could not create Propagator. Message ({}): {}".format(e.__class__.__name__, e))
        raise
        exit(1)
            
    if args.nid is None:
        nids = p.nids_to_track
        # # try to extract NIDs from tle string
        # raw_tles = tles.replace('\r', '').split('\n')
        # raw_tles = [rtle.strip() for rtle in raw_tles]
        # 
        # # do a tiny bit of error checking and extract nids
        # 
        # if  (not all([x[0] == '0' for x in raw_tles[0::3]])) or\
        #     (not all([x[0] == '1' for x in raw_tles[1::3]])) or\
        #     (not all([x[0] == '2' for x in raw_tles[2::3]])) :
        #     _print("ERROR: Malformed TLE string")
        #     exit(1)
        # 
        # nids = [int(x.split(' ')[1]) for x in  raw_tles[2::3]]
    else:
        nids = args.nid
        
    if len(nids) < 1:
        _print("ERROR: No valid TLEs and/or no NIDs. Dont know what to do")
        exit(1)
    
    if args.action == 'info':
        
        try:
            for nid in nids:
                for w in [None] if args.when is None else args.when:
                    p.print_info(nid=nid, when=_fix_timestamp(w))
            
        except Exception as e:
            _print("ERROR: action info. Message ({}):{}".format(e.__class__.__name__, e))
            exit(1)
        
        exit(0)
        
    elif args.action == 'get_all':
        if len(nids) > 1:
            _print("ERROR: get_all action only works with a single NID, you have specified {}".format(nids))
            exit(1)
        
        try:
            when = [_fix_timestamp(w) for w in args.when]
            data = p.get_all(nid=nids[0], when=when)
            data.tstamp_str = data.tstamp_str.apply(_rev_timestamp)
            
            
            if isinstance(data, pd.Series):
                data = pd.DataFrame(data).transpose()

        except Exception as e:
            _print("ERROR: action get_all. Message ({}):{}".format(e.__class__.__name__, e))
            exit(1)
            
        
    elif args.action == 'get_pass':
        
        try:
            if args.when is not None and len(args.when) != 1:
                _print("ERROR: get_pass requires when to be a single date. Use -N if you want to compute multiple passes")
                exit(1)
            data = p.get_passes(nid =nids, when=_fix_timestamp(args.when[0]) if args.when is not None else None, N=args.N, horizon=args.horizon)

            if isinstance(data, pd.Series):
                data = pd.DataFrame(data).transpose()
                data.index.name = "pass_no"

            data.rise_t = data.rise_t.apply(_rev_timestamp)
            data.max_elev_t = data.max_elev_t.apply(_rev_timestamp)
            data.set_t = data.set_t.apply(_rev_timestamp)

        except Exception as e:
            _print("ERROR: action get_pass. Message ({}):{}".format(e.__class__.__name__, e))
            exit(1)
            
        
    elif args.action == 'compute':
        if len(nids) > 1:
            _print("ERROR: compute action only works with a single NID, you have specified {}".format(nids))
            exit(1)

        if args.when is not None:
            if len(args.when) != 1:
                _print("ERROR: action compute. When must be a single value")
                exit(1)
            else:
                when = _fix_timestamp(args.when[0])
        else:
            when = None
                    
        try:
            data, psum = p.compute_pass(nid=nids[0], when=when, dt = args.dt)
            data.tstamp_str = data.tstamp_str.apply(_rev_timestamp)
            
            
        except Exception as e:
            _print("ERROR: action compute. Message ({}):{}".format(e.__class__.__name__, e))
            exit(1)
            
    else:
        _print("ERROR: Invalid action {}".format(args.action))
        exit(1)

    data = data.reset_index()
    if args.field is not None:
        try:
            data = data.loc[:, args.field]
        except Exception as e:
            _print("ERROR: Could not filter by {}. Message ({}):{}".format(args.field, e.__class__.__name__, e))
            exit(1)

    if args.print:
        print(data)
    else:
        print(data.to_csv(index=False, header=not args.no_header))
        
    exit(0)
    
def commspass():
    
    epilog="""
    
    Input
    ======
    
    commspass can take *either* a csv as input in which there must be at least
    three columns labeled az, el and range_rate, *or* it can take another commspass
    json string (the same as what is output by commspass). In the first case
    a new commspass is created, in the latter, it is modified.
    
    Adding something to pass
    ========================
    
    To add a communication or action to pass use the  -a parameter followed by
    parameters as follows:
    
    For a simple communication:
       -a byte_sequence[,retries=N][,wait=WAIT]
       
    The byte-sequence is to be specified as a HEX string in the format XX-YY-ZZ-...
    
    For an action:
       -a action[,desc=NAME][,retries=N][,wait=WAIT] [ARG [ARG ...]] [KEY=VAL [KEY=VAL ...]]
       
    Where the following optional parameters are:
       N         : Number of retires
       WAIT      : (True/False) Whether to wait for TX confirmation or not 
       NAME      : A descriptive name of an action (for logging purposes only)
       ARG       : Action arguments (action specific)
       KEY=VAL   : Action kwarguments (key=value pairs)

    """
    
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='Create/Manipulate a Communication Pass', epilog=epilog)
    
    parser.add_argument("-i", "--input", help="Input file. Omit to get input from stdin")
    parser.add_argument("-o", "--output", help="Output file. Omit will print to stdout")
    parser.add_argument("-n", "--nid", type=int, help="Norad ID to label pass with")
    parser.add_argument("-d", "--desc", type=str, help="Description to give to pass")
    parser.add_argument("-H", "--horizon", type=float, help="Visibility horizon. Default=5 deg")
    parser.add_argument("-l", "--listen", choices = ['True', 'False'], action='store', nargs='?', const="True", help="Create a listening pass")
    parser.add_argument("--dont-deduce-numeric", action="store_true", help="By default an attempt will be made to convert action arguments to numeric whenever possible. This disables that behaviour")
    parser.add_argument("-a", "--add", nargs='+', action="append", help="Add communication/action to pass")    
    parser.add_argument("-m", "--metadata", nargs=2, action='append', metavar=('key', 'value'), help="Arbitrary metadata to assign to commspass")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose progress messages displayed")
    args = parser.parse_args()
    
    if args.listen is not None:
        args.listen = eval(args.listen)
    
    def deduce_num(a):
        # a little helper function to try to guess whether a value is numeric or not
        if args.dont_deduce_numeric:
            return a
        else:
            if a.lower() == 'false':
                n = False
            elif a.lower() == 'true':
                n = True
            else:
                try:
                    n = float(a)
                    n = int(n) if n == int(n) else n
                except:
                    n = a
            return n
    
    
    def _dbg_print(*pargs, **pkwargs):
        if args.verbose:
            _print("  (debug) " + pargs[0], *(pargs[1:]), **pkwargs)
    
    if args.input is not None:
        try:
            with open(args.input, "r") as fp:
                inp = fp.read()
        except Exception as e:
            _print("ERROR: Could not read input file. Message ({}): {}".format(e.__class__.__name__, e))
            exit(1)
    else:
        _print("Enter pass data csv or commspass json. EOF (Ctrl-D) to finish")
        inp = sys.stdin.read()
    
    
    metadata = {}
    if args.metadata is not None:
        for k,v in args.metadata:
            _dbg_print("setting cp.metadata['{}'] = {}".format(k,v))
            metadata[deduce_num(k)] = deduce_num(v)
    
    # Now work out if input is a csv or a commspass json
    try:
        pdat = pd.read_csv(StringIO(inp))
        _dbg_print("Successfully interpreted input as pass data")
        
        try:
            if args.horizon is not None:
                cp =CommsPass(pdat, horizon=args.horizon)
            else:
                cp =CommsPass(pdat)
        except Exception as e:
            _print("ERROR: Could not create CommsPass. Message ({}): {}".format(e.__class__.__name__, e))
            exit(1)
        
    except Exception as e:
        try:
            cp = CommsPass.from_json(inp)
            _dbg_print("Successfully interpreted input as a CommsPass")
        except Exception as e2:
            _print("ERROR: Could not interpret input file as neither pass data ({}: {}) nor as a comms pass ({}: {})".format(e.__class__.__name__, e, e2.__class__.__name__, e2))
            exit(1)
            

    for k in ['desc', 'nid', 'listen', 'horizon']:
        v = getattr(args, k)
        if v is not None:
            _dbg_print("setting cp.metadata['{}'] = {}".format(k,v))
            cp.metadata[k] = v

    
    if args.add is not None:
        try:
            for comm in args.add:
                #
                # First parse the comm itself
                #
                cmd_args = comm[0].split(',')
                
                cmd = cmd_args[0]
                
                # Try to work out if it is a byte sequence
                if all(len(c) == 2 for c in cmd.split('-')):
                    cmd_type='bytes'
                # else assume it is an action
                else:
                    cmd_type='action'
                    
                _dbg_print("Interpreting command {} as type {}".format(cmd, cmd_type))

                retries = None
                wait    = None
                desc    = None
                for kv in cmd_args[1:]:
                    kv_split = kv.split('=')
                    if len(kv_split) != 2:
                        raise Exception("Could not parse {}. Expected key=value".format(kv))
                    
                    if   kv_split[0].lower() == 'retries':
                        retries = int(kv_split[1])
                    elif kv_split[0].lower() == 'wait':
                        wait = bool(eval(kv_split[1]))
                    elif kv_split[0].lower() == 'desc':
                        desc = kv_split[1]
                        
                _dbg_print("Command: retries = {}, wait = {}, desc = {}".format(retries, wait, desc))
                     
                    
                #
                # Then grab any additional action parameters
                #
                if len(comm) > 1 and cmd_type!='action':
                    raise Exception('byte_array does not accept args and kwargs. I got {}'.format(comm[1:]))
                    
                cargs = []
                ckwargs = {}
                for comm_arg in comm[1:]:
                    comm_arg_split = comm_arg.split('=')
                    if len(comm_arg_split) == 1:
                        cargs += comm_arg_split
                    elif len(comm_arg_split) == 2:
                        ckwargs[comm_arg_split[0]] = comm_arg_split[1] #<-- todo some type casting...?

                #
                # Now try to convert strings to float when possible
                #
                cargs2 = []
                for carg in cargs:
                    cargs2 += [deduce_num(carg)]
                
                ckwargs2 = {}
                for ckey, cval in ckwargs.items():
                    ckwargs2[deduce_num(ckey)] = deduce_num(cval)
                    
                cargs = cargs2
                ckwargs = ckwargs2
                
                _dbg_print("Command: args={}, kwargs={}".format(cargs, ckwargs))
                
                if cmd_type == 'bytes':
                    retries = 3 if retries is None else retries
                    wait = True if wait is None else wait
                    cp.add_communication(Communication(cmd, retries, wait))
                elif cmd_type == 'action':
                    retries = 0 if retries is None else retries
                    desc = "unnamed" if desc is None else desc
                    cp.add_communication(Action([cmd] + cargs, ckwargs, desc=desc, retries=retries))
                else:
                    raise Exception("Unexpected")

        except Exception as e:
            _print("ERROR: parsing communication ({}):{}".format(e.__class__.__name__, e))
            exit(1)
        
            
            
    #print(cargs, ckwargs)
    _dbg_print(str(cp))
    
    if args.output is not None:
        with open(args.output, "w") as fp:
            fp.write(cp.to_json())
    else:
        print(cp.to_json())
    
    
def schedule():
    import re
    from xmlrpclib import ServerProxy
    
    epilog = ""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='Create/Manipulate a Schedule', epilog=epilog)
    parser.add_argument("-i", "--input", nargs='+', help="Input file(s). Omit to get input from stdin")
    parser.add_argument("-o", "--output", help="Output file. Omit will print to stdout")
    parser.add_argument("--buffertime", help="Time before pass starts to initiate schedule (in s)")
    parser.add_argument("-e", "--rpc-execute", type=str, help="Try to upload and execute the schedule to the specified XMLRPC address.")
    parser.add_argument("-f", "--track-full-pass", action="store_true", help="(only with -e) Invoke scheduler with track_full_pass=True, to make antenna continue tracking until end of pass even if schedule finishes.")
    parser.add_argument("-c", "--no-compute-ant-points", action="store_true", help="(only with -e) Invoke scheduler with compute_ant_points=False, to make antenna slavishly follow the schedules")
    parser.add_argument("-s", "--rpc-stop", type=str, help="Request scheduler at specified XMLRPC address to stop execution.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose progress messages displayed on stderr")
    parser.add_argument("-p", "--print", action="store_true", help="Pretty print the schedule instead of outputting json on stdout")
    args = parser.parse_args()

    def _dbg_print(*pargs, **pkwargs):
        if args.verbose:
            _print("  (debug) " + pargs[0], *(pargs[1:]), **pkwargs)
    
    #
    # Stopping the schedule does not require anything else, so if this argument
    # is present issue the stop command then exit
    #
    if args.rpc_stop is not None:
        try:
            server = ServerProxy(args.rpc_stop, allow_none=True)
            server.stop_schedule()
            exit(0)
        except Exception as e:
            _print("ERROR: stopping schedule. Message ({}): {}".format(e.__class__.__name__, e))
            exit(1)
    
    
    #
    # Try to parse input files; either from -i or from stdin.
    #
    inp_split = []
    try:
        if args.input is not None:
            for inp in args.input:
                with open(inp, "r") as fp:
                    inp_json = fp.read()
                    
                inp_split += [inp_json]
                
                #cp += [CommsPass.from_json(cp_json)]
        else:
            _print("Enter commspass json, multiple entries accepted. EOF (Ctrl-D) to finish")
            inp = sys.stdin.read()
            inp_split = re.split('}[ \t\r\n]*{',inp)
            inp_split[0] = inp_split[0].strip()[1:]
            inp_split[-1] = inp_split[-1].strip()[:-1]
            inp_split = ['{'+s+'}' for s in inp_split]
            
            _dbg_print("Split input into {} json blocks".format(len(inp_split)))
            
    except Exception as e:
        _print("ERROR: Could not parse input. Message ({}): {}".format(e.__class__.__name__,e))
        exit(1)


    #
    # In there's only one input, first try to parse it as a schedule,
    #
    e = None
    s = None
    if len(inp_split) == 1:
        try:
            s = Schedule.from_json(inp_split[0])
        except Exception as e:
            pass

    #
    # If that failed or more than one input, try to parse as a series of
    # commspasses
    #
    if s is None:
        try:
            cp = []
            for s in inp_split:
                cp += [CommsPass.from_json(s)]
        except Exception as e2:
            e_str = "ERROR: Could not parse input"
            if e is not None:
                e_str += ", neigher as a Schedule ({}): {}, or".format(e.__class__.__name__, e)
            e_str += "as a commspass(es) ({}): {}".format(e2.__class__.__name__, e2)
            _print(e_str)
            exit(1)
            
        #_dbg_print("CommsPass(es) successfully parsed\n{}".format(cp))
        _dbg_print("{} commspass created".format(len(cp)))
        
        try:
            if args.buffertime is not None:
                s = Schedule(passes=cp, buffertime=args.buffertime)
            else:
                s = Schedule(passes=cp)
        except Exception as e:
            _print("ERROR: Could not create schedule. Message ({}): {}".format(e.__class__.__name__,e))
            exit(1)
        
    _dbg_print('{}'.format(s))
    
    if args.rpc_execute is not None:
        server = ServerProxy(args.rpc_execute, allow_none=True)
        server.execute_schedule(s.to_json(), args.track_full_pass, not args.no_compute_ant_points)        
    
    if args.output is not None:
        with open(args.output, "w") as fp:
            fp.write(s.to_json())


    #
    # Output
    #
    if args.print:
        print(str(s))
    else:
        print(s.to_json())

