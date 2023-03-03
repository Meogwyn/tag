import asyncio
import openai
import traceback
import re
import datetime
import random
import json
import os
from tag import util
from tag import ipc_serv
from tag import globs
from tag import pers
from tag import tag_prot

util.taglog_add_file_sects(__file__, ["OAI"])

pkgq = asyncio.Queue()
pkg_hdl_state = None

class PkgFatalException(Exception):
    pass

class oaiw_state():
    stat_idle = 0 # if there are no partially finished ideas
    stat_working = 1 # if there is an actively operated-on idea
    stat_success = 2
    stat_failure = 3 # pkg failed
    stat_paused = 4
#    stat_no_idea = 4 # pkg loaded, but no idea present

    def to_json(self):
        def ser(obj):
            if type(obj) == type(datetime.datetime.now()):
                return str(datetime.datetime.now())
            else:
                return obj.__dict__
        return json.dumps(self, 
                          default = ser,
                          sort_keys = True, 
                          indent = 4)
    def __init__(self, pkg = None):
        try:
            if not pkg:
                self.status = oaiw_state.stat_idle
                self.pkg = None
                self.run_id = random.randint(pow(10, 9), pow(10, 10) - 1)
                return
            elif hasattr(self, "status"):
                if self.status == stat_paused:
                    self.status = oaiw_state.stat_working
                    return

            self.status = oaiw_state.stat_working
            self.run_id = random.randint(pow(10, 9), pow(10, 10) - 1)
            self.rundate = datetime.datetime.now()
            self.pkg = pkg
            self.err = None
            self.ex = None # Temporary exception object
            self.errc = 0 # Error count
            """
            status for given idea. form: 
            {
                "idea":str(), 
                "status":"success"/"failure"/"pending"/"queued"}
                "query_data": <queries so far, if status is "pending", (or undef)>
                "path":<path where it was saved if 'success', (or undef)>
            }

            query data is an array of string results for the query
            """

            # check for duplicate ideas
            if len(self.pkg["queries"]) == 0:
                raise PkgFatalException("pkg contains no queries to be run")
            if len(self.pkg["ideas"]) == 0:
                raise PkgFatalException("pkg contains no ideas")

            for idea in pkg["ideas"]:
                if pkg["ideas"].count(idea) != 1:
                    raise Exception("duplicate idea {idea} detected in pkg (id: {pkg['id']}) ideas list")

            self.idea_stats = [] # filled as op runs. Appended upon 'pending'
            self.icur = 0
            self.qcur = 0
            util.taglog("(existent) icur: {self.icur}. All of self: self.to_json()")

            for idea in pkg["ideas"]:
                idea_stat = init_idea_stat(idea)
                self.idea_stats.append(idea_stat)
        except Exception as e:
            self.status = oaiw_state.stat_failure
            self.ex = e
            return



def set_key(key):
    openai.api_key = key

def reset_pkg_hdl_state():
    global pkg_hdl_state
    pkg_hdl_state = oaiw_state(None)


async def oai_task():
    global pkg_hdl_state
    locsects = list(util.logsects[__file__])

    paused = False
    pkg = None

    util.taglog("started oai task", 1000, locsects)

    reset_pkg_hdl_state()

    while True:
        try:
            if paused:
                util.taglog(f"paused - waiting...", 5000, locsects)
                await asyncio.sleep(1)
                continue

            if pkg_hdl_state.status == oaiw_state.stat_idle:
                pkg = await pkgq.get()
                util.taglog(f"acquired pkg {pkg}", 5000, locsects)

            await handle_pkg(pkg)
            tag_prot.pkg_success(pkg_hdl_state.pkg["id"])

            pers.dump_pkg_hdl_state(pkg_hdl_state)
            reset_pkg_hdl_state()
        except asyncio.CancelledError as e:
            if str(e) == "pause":
                util.taglog(f"package processing paused on pkg {pkg}", 2000, 
                            locsects)
                paused = True
            elif str(e) == "unpause":
                util.taglog(f"package processing unpaused on pkg {pkg}", 2000, 
                            locsects)
                paused = False
            else:
                raise
            """
            TODO: auto-pkg-state dump code
            """
        except PkgFatalException as e:
            if pkg:
                tag_prot.pkg_failure(pkg["id"], repr(e))
            pers.dump_pkg_hdl_state(pkg_hdl_state)
            reset_pkg_hdl_state()



def pkg_hdl_state_lookup_idea(idea):
    for x in pkg_hdl_state.idea_stats:
        if x["idea"] == idea:
            return x
        
    raise Exception(f"failed to find {idea} in idea_stats")
"""
Queue an idea for operation
"""
def init_idea_stat(idea):
            out = {
                "idea": idea,
                "status": "queued",
            }
            return out
def prep_idea_stat(idea_stat):
    global pkg_hdl_state
    new_idea_stat = dict(idea_stat)

    new_idea_stat["status"] = "pending"
    new_idea_stat["query_data"] = []

    pkg_hdl_state.idea_stats.remove(idea_stat)
    pkg_hdl_state.idea_stats.append(new_idea_stat)

    return new_idea_stat
"""
On success, save to path, modify params as needed, remove unneeded data
"""
def fin_idea_stat(idea_stat, status, err = None):
    global pkg_hdl_state
    

    new_idea_stat = dict(idea_stat)

    pers.dump_pkg_hdl_state(pkg_hdl_state) # For now, dump after every idea

    if status == "failure":
        new_idea_stat["status"] = "failure"
        if "path" in new_idea_stat:
            del new_idea_stat["path"]
        if err:
            new_idea_stat["err"] = err

        tag_prot.idea_failure(new_idea_stat["idea"], err)
    elif status == "success":
        new_idea_stat["status"] = "success"

        ipath = pkg_hdl_state.pkg["output_dir"] + f"/{new_idea_stat['idea']}"

        if pkg_hdl_state.pkg["overwrite"]:
            os.makedirs(ipath, exist_ok = True)
        else:
            os.makedirs(ipath)

        pers.write_idea_stat(pkg_hdl_state.pkg["queries"], 
                             new_idea_stat["query_data"], 
                             ipath + "/oai_output.txt")
        tag_prot.idea_success(new_idea_stat["idea"])
    else:
        raise Exception("...what...")

    pkg_hdl_state.idea_stats.remove(idea_stat)
    pkg_hdl_state.idea_stats.append(new_idea_stat)

    return new_idea_stat



    """
    It's a shame I can't localize the writing logic to here, but eh
    """

"""
Parses an OPAL prompt, automatically substituting the corresponding values from
pkg_hdl_state

OPAL desc: Just the normal query, unless one means to plug in a result from a 
previous query, in which case it is inserted using ' $<number of query> ' 
note the spaces, (since I was too lazy to parse brackets n' stuff) though EOL
works as a delimiter as well.

One special thing, btw: $i inserts the original idea. I guess this is mostly 
useful for the first prompt

Also I don't know what will happen should the ai generate a valid substitution...
I hope it won't, but the worst that could happen is a freeze of the program


args:
prompt: unprocessed prompt
dest_q: destination query as defined in schemas.py (for inp cb funcs)
idea_stat: for original idea, if needed, and query data

"""
def parse_opal(dest_q, idea_stat):
    locsects = util.logsects[__file__]
    """
    group 3 - number
    group 4 - title (i)
    """
    pat = re.compile('(:?\s|^)(\\$([\d]+(:?\s|$))|\\$(i(:?\s|$)))')
    prev = None
    tot_its = 0

    out = dest_q["prompt"]
    
    while True:
        tot_its = tot_its + 1
        if tot_its > 1000:
            raise Exception("likely entered infinite sub loop")

        if prev:
            x = pat.search(out, prev.start() + 1)
        else:
            x = pat.search(out)


        if not x:
            util.taglog(f"replacement done. res: {out}", 5000, locsects)
            break
        util.taglog(f"match: '{x.group(0)}'")
        prev = x

        if x.group(3):
            qdata = query_data_get_idx(dest_q, int(x.group(3)), 
                                                   idea_stat["query_data"])
            out = out.replace(x.group(0), qdata)
        elif x.group(5):
            out = out.replace(x.group(0), " " + idea_stat["idea"] + " ")

        """
        This prevents weird symbols in the beginning of the response
        """
        if not out.endswith(".\n\n"):
            out = out + ".\n\n"

    return out


"""
Retrieve + format src_idx in prep for target query

1. Look up src_idx in current idea's query_data
2. Look up dest_idx in the pkg query list and apply inp_cb_map
"""
def query_data_get_idx(dest_q, src_idx, query_data):
    util.taglog(f"gathering input from query {src_idx} for target {dest_q}")

    out = query_data[src_idx] 

    if "inp_cb_map" in dest_q:
        for cb in dest_q["inp_cb_map"]:
            if cb.idx == src_idx:
                out = proc.exec_proc(cb.cb_name, out)

    return out

"""
sets query_data for idea

correct usage presumes that queries are processed in the order they are specified

otherwise, there would need to be an additional 'idx' parameter in the query_data
list
"""
def push_query_data(data, idea_stat):
    global pkg_hdl_state
    new_idea_stat = dict(idea_stat)

    new_idea_stat["query_data"].append(data)

    pkg_hdl_state.idea_stats.remove(idea_stat)
    pkg_hdl_state.idea_stats.append(new_idea_stat)

    return new_idea_stat
"""
Executes a query, automatically taking care of modifying query_data as needed.
Must be called on queries in the order they are specified in in pkg["queries"].
"""
async def exec_query(query, idea_stat):
    # phase 1: parse opal prompt, substituting inputs
    # phase 2: shove into oai, using oai_conf_gen (or whatever) where applicable
    # phase 3: set output
    locsects = util.logsects[__file__]

    util.taglog(f"executing query '{query}' w/ idea_stat '{idea_stat}'", 
                3000, 
                locsects)

    oai_config = query["oai_config"]
    oai_config["prompt"] = parse_opal(query, idea_stat)
    oai_out = None


    for param in pkg_hdl_state.pkg["oai_config_gen"]:
        if param not in oai_config:
            oai_config[param] = pkg_hdl_state.pkg["oai_config_gen"][param]

    oai_out = await openai.Completion.acreate(**oai_config)
    oai_out = oai_out.choices[0].text

    if "out_cb" in query:
        oai_out = proc.exec_proc(query["out_cb"], oai_out)

    idea_stat = push_query_data(oai_out, idea_stat)


"""
gets current idea_stat of idea
"""
def get_idea_stat(idea):
    for idea_stat in pkg_hdl_state.idea_stats:
        if idea_stat["idea"] == idea:
            return idea_stat
    raise Exception(f"idea_stat not found for idea '{idea}'")


async def handle_pkg(pkg):
    global pkg_hdl_state
    locsects = util.logsects[__file__]
    idea_stat = None

    # Rare case when we don't work off of exceptions
    # TODO: convert to simply a one-time __new__() call with __init__() calls
    # as needed
    pkg_hdl_state = oaiw_state(pkg)
    tag_prot.pkg_start(pkg_hdl_state)
    if not openai.api_key:
        pkg_hdl_state.status = oaiw_state.stat_failure
        raise PkgFatalException("openai api key not provided (use 'set_key' call)")

    if pkg_hdl_state.status == oaiw_state.stat_failure:
        raise pkg_hdl_state.ex

    while pkg_hdl_state.icur < len(pkg["ideas"]):
        try:
            if pkg_hdl_state.errc > pkg_hdl_state.pkg["max_failures"]:
                raise PkgFatalException("max_failures exceeded")
            pers.dump_pkg_hdl_state(pkg_hdl_state) 
            idea = pkg_hdl_state.pkg["ideas"][pkg_hdl_state.icur]
            idea_stat = get_idea_stat(idea)
            if idea_stat["status"] == "queued":
                idea_stat = prep_idea_stat(idea_stat)
            elif idea_stat["status"] != "pending":
                pkg_hdl_state.icur = pkg_hdl_state.icur + 1
                continue

            while pkg_hdl_state.qcur < len(pkg["queries"]):
                await exec_query(pkg["queries"][pkg_hdl_state.qcur], idea_stat) 
                util.taglog(f"executed query. qcur: {pkg_hdl_state.qcur}. len:{len(pkg['queries'])}", 5000, locsects)
                pkg_hdl_state.qcur = pkg_hdl_state.qcur + 1

            pkg_hdl_state.qcur = 0

            fin_idea_stat(idea_stat, "success")
            util.taglog(f"idea_stat 3: {idea_stat}")
            idea_stat = None

            pkg_hdl_state.icur = pkg_hdl_state.icur + 1
        except asyncio.CancelledError:
            raise
        except PkgFatalException:
            pkg_hdl_state.status = oaiw_state.stat_failure
            pkg_hdl_state.error = repr(PkgFatalException)
            raise
        except Exception as e:
            if idea_stat:
                fin_idea_stat(idea_stat, "failure", repr(e))
            else:
                raise PkgFatalException(f"An exception ({repr(e) + traceback.format_exc()}) was raised in handle_pkg in the absence of an idea")
        
    pkg_hdl_state.status = oaiw_state.stat_success

def unfreeze_pkg_state():
    pass
    # For future: reset errc
    # also eventually use setattr to reconstruct the class
    # also make sure a package cannot get dumped if it is in stat_idle...

"""
Call to schedule a package for handling
"""
def schedule_pkg(pkg):
    pkgq.put_nowait(pkg)
def pause():
    pkg_hdl_state.status = oaiw_state.stat_paused
