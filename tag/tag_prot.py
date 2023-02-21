"""
impementation of parser, according to tag_prot
"""

import asyncio
from tag import util
from tag import ipc_serv
from tag import globs
import json

parseq = asyncio.Queue()

util.taglog_add_file_sects(__file__, ["PARSER"])

def push_parseq_str(cmdstr):
    locsects = util.logsects[__file__]
    try:
        parseq.put_nowait(json.loads(cmdstr))
    except json.decoder.JSONDecodeError as e:
        util.taglog(f"Received invalid JSON. Error: {e}", 1000, locsects)

async def parse_task():
    locsects = util.logsects[__file__]
    util.taglog("started tag_prot parser", 1000, locsects)
    while True:
        cmd = await parseq.get()
        await exec_cmd(cmd)

"""
executes dict-form command
"""
async def exec_cmd(cmd):
    locsects = util.logsects[__file__]
    util.taglog(f"attempting to exec cmd: {json.dumps(cmd)}", 5000, locsects)
    if not "type" in cmd:
        util.taglog(f"command lacks type! cmd: {cmd}", 1000, locsects)
        return
    match (cmd["type"]):
        case "test":
            util.taglog(f"test!", 1, locsects)
            return
        case "ping":
            ipc_serv.ipc_send_dict({"type":"ping", 
                     "tag_prot_vers":globs.Globs["tag_prot_vers"], 
                     "tag_vers":globs.Globs["tag_vers"]
                     })
        case "pause":
            pass
        case "resume":
            pass
        case "reanimate":
            pass
        case "hibernate":
            pass
        case "cancel":
            pass
        case "start_fl":
            pass
        case "start_lst":
            pass
        case "status":
            pass
        case "export_run":
            pass
        case "settings_profile_param":
            pass
        case "pkg_profile_param":
            pass
        case "job_run":
            pass
        case "all_job_runs":
            pass
        case "all_settings_profiles":
            pass
        case "all_pkg_profiles":
            pass
        case "create_pkg_profile":
            pass
        case "edit_pkg_profile":
            pass
        case "remove_pkg_profile":
            pass
        case "create_settings_profile":
            pass
        case "edit_settings_profile":
            pass
        case "remove_pkg_profile":
            pass
        case _:
            util.taglog(f"command {cmd['type']} not found!")
            return
            

