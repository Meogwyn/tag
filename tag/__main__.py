# Initialization and general control (message parsing)

import asyncio
import signal
import datetime
import sys
import os
import re
from os.path import exists
import dotenv
#from tag.util import util.taglog
from tag import util
from tag import globs

from tag.tag_prot import parse_task
from tag.ipc_serv import ipc_serv_task

myenv = {}

util.taglog_add_file_sects(__file__, ["MAIN"])

"""
The beginning, middle and end
"""
async def main():
    #no logging before these two
    load_envvars()
    set_globs()

    util.taglog(f"[START {datetime.datetime.now()}]", depth = 1)

    signal.signal(signal.SIGINT, util.sigint_hdl)

    util.taglog(f"env vars:{globs.Globs['env']}", sects = util.logsects[__file__], depth = 5000)

    await asyncio.gather(ipc_serv_task(), parse_task())
    while True:
        util.taglog('lol', sects = util.logsects[__file__])
        await asyncio.sleep(1)

"""
NO LOGGING AT ALL IN THIS FUNC

loads env vars (duh)
sets globs.Globs["env"] to final list

(order: cmd-line, env)
"""
def load_envvars():
    global Globs
    if not os.path.exists(".env"):
        open(".env", "w").close() # simple way to create env file
    globs.Globs["env"] = dotenv.dotenv_values(".env")
    globs.Globs["env"].update(os.environ) #cmd-line overwrites vars from 

"""
NO LOGGING AT ALL IN THIS FUNC

meant to be called shortly after load_envvars

reacts to envvars as much as is possible immediately after loading them
"""

def set_globs():
    global Globs

    repat = re.compile("\s*")

    if "TAG_LOGDEPTH" in globs.Globs["env"]:
        globs.Globs["logdepth"] = int(globs.Globs["env"]["TAG_LOGDEPTH"])
    else:
        globs.Globs["logdepth"] = 5000

    #format of TAG_LOGSECTS_* is `"<SECT>"[, ...]`
    #if neither is set, all sections are included by default

    #logsects[__file__] to exclude in util.taglog() calls
    if "TAG_LOGSECTS_INCL" in globs.Globs["env"]:
        globs.Globs["logsects_incl"] = (re.sub(repat, "", globs.Globs["env"]["TAG_LOGSECTS_INCL"])).split(',')
    #logsects[__file__] to exclude in util.taglog() calls
    elif "TAG_LOGSECTS_EXCL" in globs.Globs["env"]:
        globs.Globs["logsects_excl"] = (re.sub(repat, "", globs.Globs["env"]["TAG_LOGSECTS_EXCL"])).split(',')
    if "TAG_LOGSTDERR" in globs.Globs["env"]:
        if globs.Globs["env"]["TAG_LOGSTDERR"].lower() == "true":
            re.sub(repat, "", globs.Globs["env"]["TAG_LOGSTDERR"])
            globs.Globs["logstderr"] = True
        if globs.Globs["env"]["TAG_LOGSTDERR"].lower() == "false":
            globs.Globs["logstderr"] = False
    else:
        globs.Globs["logstderr"] = True

    if "TAG_LOGFILE_MODE" in globs.Globs["env"]:
        globs.Globs["logfile_mode"] = globs.Globs["env"]["TAG_LOGFILE_MODE"]
    else:
        globs.Globs["logfile_mode"] = "r+"


    if "TAG_LOGFILE" in globs.Globs["env"]:
        globs.Globs["logfile"] = open(globs.Globs["env"]["TAG_LOGFILE"], globs.Globs["logfile_mode"])

    if "TAG_TCP_HOST" in globs.Globs["env"]:
        globs.Globs["tcp_host"] = globs.Globs["env"]["TAG_TCP_HOST"]
    else:
        globs.Globs["tcp_host"] = "localhost" 

    if "TAG_TCP_PORT" in globs.Globs["env"]:
        globs.Globs["tcp_port"] = int(globs.Globs["env"]["TAG_TCP_PORT"])
    else:
        globs.Globs["tcp_port"] = 15324

if __name__ == "__main__":
    asyncio.run(main())
