"""
impementation of parser, according to the tag_prot protocol (which was designed 
by the author of this code, so don't look for any documentation for it online)
"""

import asyncio
import traceback
from tag import schemas
from tag import util
from tag import ipc_serv
from tag import globs
from tag import pers
from tag import oai_stuff
import json

parseq = asyncio.Queue()


util.taglog_add_file_sects(__file__, ["PARSER"])
def idea_success(idea):
    ipc_serv.ipc_send_dict({"type":"idea_success", "data":idea})
def idea_failure(idea, error_desc):
    ipc_serv.ipc_send_dict({"type":"idea_failure", "err":{"idea": idea, "desc": error_desc}})

def pkg_success(pkg_id):
    ipc_serv.ipc_send_dict({"type":"pkg_success", "data":pkg_id})
def pkg_failure(pkg_id, error_desc):
    ipc_serv.ipc_send_dict({"type":"pkg_failure", "err":{"pkg_id": pkg_id, "desc": error_desc}})



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
    ipc_serv.ipc_send_dict({"type":ctype, "err":{"desc": err}})

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
        case "set_key":
            try:
                req_args = ["key"]
                val_args(cmd["data"], req_args)
                oai_stuff.set_key(cmd["data"]["key"])
                resp_cmd_succ(cmd["type"], None) 
            except Exception as e:
                resp_cmd_err(cmd["type"], repr(e)) 
        case "start":
            try:
                req_args = ["id"]

                val_args(cmd["data"], req_args)

                pkg = pers.get_pkg_config(cmd["data"]["id"])
                oai_stuff.schedule_pkg(pkg)

                resp_cmd_succ(cmd["type"], None) #ret is created config entry

            except Exception as e:
                resp_cmd_err(cmd["type"], repr(e) + traceback.format_exc()) 
#                resp_cmd_err(cmd["type"], repr(e)) 
                return

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
                req_args = ["pkgc"] # shell pkgc without id, etc
                opt_args = ["ideas_files"]


                """
                if 'params' are missing, a default profile is created
                if 'params' is present, but lacks some possible parameters, defualt
                values are substituted
                """

                val_args(cmd["data"], req_args, opt_args)

                if "ideas_files" in cmd["data"]:
                    ret = pers.create_pkg_config(cmd["data"]["pkgc"], cmd["data"]["ideas_files"])
                else:
                    ret = pers.create_pkg_config(cmd["data"]["pkgc"])

                resp_cmd_succ(cmd["type"], ret) #ret is created config entry
            except Exception as e:
                resp_cmd_err(cmd["type"], repr(e) + traceback.format_exc()) 
#                resp_cmd_err(cmd["type"], repr(e)) 
                return
        case "remove_pkg_config":
            try:
                req_args = ["id"]

                val_args(cmd["data"], req_args)

                ret = pers.remove_pkg_config(cmd["data"]["id"])
            except Exception as e:
                    resp_cmd_err(cmd["type"], repr(e))
                    return
            resp_cmd_succ(cmd["type"], ret) # ret is resultant pkg config file
        case "update_pkg_config":
            try:
                req_args = ["id"]
                opt_args = ["queries"] 

                val_args(cmd["data"], req_args, opt_args)

                ret = pers.update_pkg_config(cmd["data"]["id"], cmd["data"]["queries"])
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
            

