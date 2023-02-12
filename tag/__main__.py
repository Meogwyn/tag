# Initialization and general control (message parsing)

import asyncio
import sys
import os
import re
from os.path import exists
import dotenv
from .util import *
from .globs import *

myenv = {}
logsects = []

"""
The beginning, middle and end
"""
async def main():
    #no logging before these two
    load_envvars()
    set_globs()

    logsects.append("MAIN")

    taglog("starting tag!", sects = logsects, depth = 1000)
    taglog(f"env vars:{Globs['env']}", sects = logsects, depth = 5000)

    while True:
        taglog('lol', sects = logsects)
        logsects.remove("MAIN")
        logsects.append("SHMAIN")
        await asyncio.sleep(1)
        taglog('lol', sects = logsects)
        logsects.remove("SHMAIN")
        logsects.append("MAIN")
        await asyncio.sleep(1)

"""
NO LOGGING AT ALL IN THIS FUNC

loads env vars (duh)
sets Globs["env"] to final list

(order: cmd-line, env)
"""
def load_envvars():
    global Globs
    if not os.path.exists(".env"):
        open(".env", "w").close() # simple way to create env file
    Globs["env"] = dotenv.dotenv_values(".env")
    Globs["env"].update(os.environ) #cmd-line overwrites vars from 

"""
NO LOGGING AT ALL IN THIS FUNC

meant to be called shortly after load_envvars

reacts to envvars as much as is possible immediately after loading them
"""

def set_globs():
    global Globs

    repat = re.compile("\s*")

    if "TAG_LOGDEPTH" in Globs["env"]:
        Globs["logdepth"] = int(Globs["env"]["TAG_LOGDEPTH"])
    else:
        Globs["logdepth"] = 5000

    #format of TAG_LOGSECTS_* is `"<SECT>"[, ...]`
    #if neither is set, all sections are included by default

    #logsects to exclude in taglog() calls
    if "TAG_LOGSECTS_INCL" in Globs["env"]:
        Globs["logsects_incl"] = (re.sub(repat, "", Globs["env"]["TAG_LOGSECTS_INCL"])).split(',')
    #logsects to exclude in taglog() calls
    elif "TAG_LOGSECTS_EXCL" in Globs["env"]:
        Globs["logsects_excl"] = (re.sub(repat, "", Globs["env"]["TAG_LOGSECTS_EXCL"])).split(',')

    if "TAG_LOGSTDERR" in Globs["env"]:
        if Globs["env"]["TAG_LOGSTDERR"].to_lower() == "true":
            repat.sub("")
            Globs["logstderr"] = True
        if Globs["env"]["TAG_LOGSTDERR"].to_lower() == "true":
            Globs["logstderr"] = False
    else:
        Globs["logstderr"] = True

    if "TAG_LOGFILE_MODE" in Globs["env"]:
        Globs["logfile_mode"] = Globs["env"]["TAG_LOGFILE_MODE"]
    else:
        Globs["logfile_mode"] = "r+"


    if "TAG_LOGFILE" in Globs["env"]:
        Globs["logfile"] = open(Globs["env"]["TAG_LOGFILE"], Globs["logfile_mode"])

if __name__ == "__main__":
    asyncio.run(main())
