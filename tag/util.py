import sys

from .globs import *

"""
A standard practice across this project will be to have a file-scope
global var (named logsects, for example), to which one will be able to 
add/remove sects (preferably defined as consts in the beginning of the file)

depth - depth to filter against global depth
sects - list of strings to prepend to logger and do filtering over
"""

def filter_depth(depth):
    if Globs["logdepth"] == None:
        return True
    if depth > Globs["logdepth"]:
        return False
    else:
        return True
def filter_sects(sects):
    for sect in sects:
        if Globs["logsects_incl"]:
            if sect not in Globs["logsects_incl"]:
                return False
        if Globs["logsects_excl"]:
            if sect in Globs["logsects_excl"]:
                return False
    return True
"""
Returns True or False depending on whether a logline is respectively fit or 
not for logging
"""
def logfilter(depth, sects):
    if depth:
        if not filter_depth(depth):
            return False
    print(f'filtering sects: incl:{Globs["logsects_incl"]} excl:{Globs["logsects_excl"]}')
    if sects:
        if not filter_sects(sects):
            print(f'filter rejected sects {sects}')
            return False
    return True
"""
NO LOGGING IN THIS FUNCTION

prints a log entry, optionally prefixed with one or several section 
identifiers, and filtered based on depth
"""
def taglog(rawstr, depth=5000, sects=None):
    if not logfilter(depth, sects):
        return

    logstr = ""

    if sects is not None:
        for sect in sects:
            logstr += f"[{sect}]"
    else:
        logstr += f"[UNDEF]"


    logstr += f" {rawstr}"

    if Globs["logfile"]:
        Globs["logfile"].seek(0, 2)
        Globs["logfile"].write(logstr)
    if Globs["logstderr"]:
        print(logstr, file=sys.stderr)

def clean_exit(code):
    exit(code)
