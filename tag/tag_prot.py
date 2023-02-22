"""
impementation of parser, according to the tag_prot protocol (which was designed 
by the author of this code, so don't look for any documentation for it online)
"""

import asyncio
import traceback
from tag import util
from tag import ipc_serv
from tag import globs
from tag import pers
import json

parseq = asyncio.Queue()

util.taglog_add_file_sects(__file__, ["PARSER"])

def push_parseq_str(cmdstr):
    locsects = util.logsects[__file__]
    try:
        parseq.put_nowait(json.loads(cmdstr))
    except json.decoder.JSONDecodeError as e:
        util.taglog(f"received invalid JSON; error: {e}", 1000, locsects)

async def parse_task():
    locsects = util.logsects[__file__]
    util.taglog("started tag_prot parser", 1000, locsects)
    while True:
        cmd = await parseq.get()
        await exec_cmd(cmd)

"""
Issues a successful response to a received command
"""
def resp_cmd_succ(ctype, data):
    if data == None:
        ldata = {}
    else:
        ldata = data
    ipc_serv.ipc_send_dict({"type":ctype, "data":ldata})
def resp_cmd_err(ctype, err):
    ipc_serv.ipc_send_dict({"type":ctype, "err":err})

"""
Verifies all args from req_args are in args

returns True if all req_args are present
return a missing arg if arg is missing
"""

def val_args(args, req_args = None, opt_args = None):
    if not req_args:
        req_args = []
    if not opt_args:
        opt_args = []

    for arg in req_args:
        if arg not in args:
            raise Exception(f"required argument '{arg}' is missing")
    for arg in args:
        if arg not in req_args + opt_args:
            raise Exception(f"invalid argument '{arg}'")

    

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
        case "ping": #TODO place data in 'data' key
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
            ret = pers.all_settings_profiles()
            resp_cmd_succ(cmd["type"], ret)
        case "all_pkg_configs":
            ret = pers.all_pkg_configs()
            resp_cmd_succ(cmd["type"], ret)
        case "create_pkg_config":
            ret = None
            try: 
                req_args = ["name"]
                opt_args = ["queries"] 
                """
                if 'params' are missing, a default profile is created
                if 'params' is present, but lacks some possible parameters, defualt
                values are substituted
                """

                val_args(cmd["data"], req_args, opt_args)

                if "queries" in cmd["data"]:
                    ret = pers.create_pkg_config(cmd["data"]["name"], 
                                                 cmd["data"]["queries"]) 
                else:
                    ret = pers.create_pkg_config(cmd["data"]["name"], None) 

            except Exception as e:
                resp_cmd_err(cmd["type"], repr(e) + traceback.format_exc()) 
                return
            resp_cmd_succ(cmd["type"], ret) #ret is created config entry
        case "remove_pkg_config":
            try:
                req_args = ["id"]

                val_args(cmd["data"], req_args)

                ret = pers.remove_pkg_config(cmd["data"]["id"])
            except Exception as e:
                    resp_cmd_err(cmd["type"], repr(e))
                    return
            resp_cmd_succ(cmd["type"], ret) # ret is resultant pkg config file
        case "create_settings_profile":
            pass
        case "edit_settings_profile":
            pass
        case "remove_settings_profile":
            pass
        case _:
            util.taglog(f"command {cmd['type']} not found!")
            return
            

