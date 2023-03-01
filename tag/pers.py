"""
functions for interacting with persistent data (viz. pkg configs,
settings and job runs information
"""
from tag import globs
from tag import util
from tag import schemas
import os
import jsonschema
import random
import json

util.taglog_add_file_sects(__file__, ["PERS"])

"""
Write the contents of an idea_stat to the file
"""
def dump_pkg_hdl_state(pkg_hdl_state):
    locsects = list(util.logsects[__file__])
    util.taglog(f"dumping package state {pkg_hdl_state.to_json()}", 5000, locsects)
    if pkg_hdl_state.pkg:
        with open(f"pers/pkg_runs/{pkg_hdl_state.run_id}", "w") as fl:
            fl.write(pkg_hdl_state.to_json())
def write_idea_stat(queries, query_data, outfl):
    if len(queries) != len(query_data):
        raise Exception(f"size of query_data ({len(query_data)}) differs from size of queries ({len(queries)})!")
    with open(outfl, "x") as fl:
        for i in range(len(queries)):
            fl.write(f"{i} -- {queries[i]['out_header']}\n\n")
            fl.write(f"{query_data[i]}\n\n")



"""
Validate that a pkg config conforms to the prototype format
"""
def val_pkg_config(pkgc):
    jsonschema.validators.validate(pkgc, schemas.pkg_config_schema)

def gen_settings():
    temp = {"test_setting":"test"}
    with open("pers/settings.json", "w+") as fl:
        json.dump(temp, fl, indent = 4)
def all_settings_profiles():
    locsects = list(util.logsects[__file__])
    if not os.path.exists("pers/settings.json"):
        util.taglog(f"settings file missing! generating new one", 1000, locsects)
        gen_settings()
    with open("pers/settings.json", "r+") as fl:
        raw = fl.read()
        if len(raw) == 0:
            util.taglog(f"settings file empty! generating new one", 1000, 
                        locsects)
            gen_settings()
            return json.load(fl)
        return json.loads(raw)

"""
Generates empty pkg_presets file with empty pkg preset array.
"""
def gen_pkg_configs():
    temp = []
    with open("pers/pkg_configs.json", "w+") as fl:
        json.dump(temp, fl, indent = 4)
"""
Returns list with all pkg configs, which, by the way, must be .json files
"""
def all_pkg_configs():
    locsects = list(util.logsects[__file__])

    out = []

    pkgc_fl_list = os.listdir('pers/pkg_configs')
    for fname in pkgc_fl_list:
        with open('pers/pkg_configs/' + fname, "r") as fl:
            out.append(json.load(fl))
    return out
    
"""
generates default pkg config with specified name.
Necessarily initializes ALL possible params

Parameter explanations:

for oai stuff, see oai docs

prompt, *_cb - prompt that gets sent to oai with $x corresponding to the output 
of query with index x (starting from 0), after that query's out_cb and this query's 
inp_cb_gen, and, optionally, the corresponding inp_cb_map element have been 
applied to it. '$t' corresponds to the original title. For example:

Callbacks specified in inp_cb_map are defined in the oai_cbs.py file, and
pushed into a container class that has all of 'em.
[
    {
        prompt: "Generate a clickbaity version of this title: $t"
        ...params
    },
    {
        prompt: "Generate an article outline based on the following title: $0
        out_cb: "outline_out_cb" # To separate properly into lines, for example
    },
    {
        prompt: "Do some weird stuff with this title:$0 and this outline$1:
        inp_cb_map:map([
            {
                "query_idx":0,
                "callback":"owoify"
                "before_gen": True/False
            },
            {
                "query_idx":1,
                "callback":"condense"
                "before_gen": True/False
            }
        ])
    },
    ...
]

example 'queries':
"queries": [
    {
        "prompt": "provide a random number between 1 and 4 * 10 ^ 13" ,
        "inp_cb_gen": None,
        "inp_cb_map": None,
        "out_cb": None,

        # oai stuff
        "oai_config": {
            "engine": "text-davinci-3",
            "max_tokens": 1024,
            "temperature": 0.5,
            "frequency_penalty": 1,
            "presence_penalty": 1
        }
    },
    {
        "prompt": "name $0 banana types ,
        "inp_cb_gen": None,
        "inp_cb_map": None,
        "out_cb": None,

        # oai stuff
        "oai_config": {
            "engine": "text-davinci-3",
            "max_tokens": 1024,
            "temperature": 0.5,
            "frequency_penalty": 1,
            "presence_penalty": 1
        }
    }
]
"""

def write_pkg_config(config):
    locsects = list(util.logsects[__file__])
    """
    Shoddy but probably works
    """
    with open(f"pers/pkg_configs/{config['name']}-{config['id']}.json", "w") as fl:
        json.dump(config, fl, indent = 4)
    return config
"""
Validates format of queries to be added to a pkg config

Raises an Exception() if it finds an error in the format
"""
def val_queries(queries):
    req_keys = ["prompt", "oai_config"]

    if not type(queries) == list:
        raise Exception("'queries' argument should be a list")
    for query in queries:
        for key in req_keys:
            if not key in query:
                raise Exception(f"query '{query}' missing key {key}")
    

"""
Same as 'id', except file gets overwritten, rather than created
"""
def update_pkg_config(pkg_config, pkg_id):
    locsects = list(util.logsects[__file__])

    pkgc = dict(pkg_config)
    
    if "ideas_files":
        load_ideas_files(pkgc, ideas_files)

    val_pkg_config(pkgc)

    fl = lookup_pkg_config(pkg_id)
    json.dump(pkg_config, fl, indent = 4)
    return pkg_config
"""
Copies over ideas into the specified pkg config from a provided list of ideas
files

Note: no validation is performed on ideas files to make sure the strings are in
appropriate form.
"""
def load_ideas_files(pkgc, ideas_files):
    for fname in ideas_files:
        if not os.path.exists(fname):
            raise Exception(f"ideas file path {fname} doesn't exist")
        with open(fname, "r") as fl:
            while True:
                idea = fl.readline()
                if idea == "":
                    break
                idea.strip()
                pkgc["ideas"].append(idea)
"""
Creates package config with args according to pkg_config_schema in schemas.py
and an optional 'ideas_files' arg which complements 'manually' provided ideas with
ones from the specified ideas files

pkg_config is raw data provided according to pkg_config_schema, and simply copied
over
"""
def create_pkg_config(pkg_config, ideas_files = None):
    locsects = list(util.logsects[__file__])

    pkgc = dict(pkg_config)
    pkgc["id"] = random.randint(pow(10, 9), pow(10, 10) - 1)
    
    if ideas_files:
        load_ideas_files(pkgc, ideas_files)

    val_pkg_config(pkgc)
    util.taglog(f"about to create following pkg config {pkgc}", 5000, locsects)

    return write_pkg_config(pkgc)

"""
Returns open file if found. Raises exception if not found.

todo: working directory???
"""
def lookup_pkg_config(pkg_id):
    pkgc_fl_list = os.listdir("pers/pkg_configs")
    for fname in pkgc_fl_list:
        fl = open("pers/pkg_configs/" + fname, "r")
        jsonraw = json.load(fl)
        if jsonraw["id"] == pkg_id:
            return fl
        fl.close()

    raise Exception(f"pkg_config with id {pkg_id} not found")

def get_pkg_config(pkg_id):
    pkgc_fl_list = os.listdir("pers/pkg_configs")
    for fname in pkgc_fl_list:
        with open("pers/pkg_configs/" + fname, "r") as fl:
            out = json.load(fl)
            if out["id"] == pkg_id:
                return out

    raise Exception(f"pkg_config with id {pkg_id} not found")

"""
removes pkg config file with specified id
"""
def remove_pkg_config(pkg_id):
    locsects = list(util.logsects[__file__])
    found = False

    util.taglog(f"attempting to remove pkg with id {pkg_id}", 3000, locsects)

    target = lookup_pkg_config(pkg_id)
    util.taglog(f"removing pkg config file {target.name}", 3000, locsects)
    os.remove(target.name)
