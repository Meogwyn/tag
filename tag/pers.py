"""
functions for interacting with persistent data (viz. pkg configs,
settings and job runs information
"""
from tag import globs
from tag import util
import random
import json
import os.path as path

util.taglog_add_file_sects(__file__, ["IPC_SERV"])

def gen_settings():
    temp = {"test_setting":"test"}
    with open("pers/settings.json", "w+") as fl:
        json.dump(temp, fl, indent = 4)
def all_settings_profiles():
    locsects = list(util.logsects[__file__])
    if not path.exists("pers/settings.json"):
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
Returns all pkg configs currently defined
"""
def all_pkg_configs():
    locsects = list(util.logsects[__file__])
    if not path.exists("pers/pkg_configs.json"):
        util.taglog(f"pkg config file missing! generating new one", 1000, 
                    locsects)
        gen_pkg_configs()
    with open("pers/pkg_configs.json", "r+") as fl:
        raw = fl.read()
        if len(raw) == 0:
            util.taglog(f"pkg config file empty! generating new one", 1000, 
                        locsects)
            gen_pkg_configs()
            return json.load(fl)
        return json.loads(raw)
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

"""
def empty_pkg_config(name):
    pkgc = {
        "name": name,
        "id": None,
        "queries": [
            {
                "prompt": None ,
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
    }
    return pkgc

def write_pkg_config(config):
    locsects = list(util.logsects[__file__])
    if not path.exists("pers/pkg_configs.json"):
        util.taglog(f"pkg config file missing! generating new one", 1000, 
                    locsects)
        gen_pkg_configs()
    with open("pers/pkg_configs.json", "r+") as fl:
        raw = fl.read()
        if len(raw) == 0:
            util.taglog(f"pkg config file empty! generating new one", 1000, 
                        locsects)
            gen_pkg_configs()
            
        rawjson = json.loads(raw)

        for temp in rawjson:
            if config["name"] == temp["name"]:
                raise Exception(f"pkg config with name {temp['name']} already exists")

        rawjson.append(config)
        fl.truncate()
        fl.seek(0)
        json.dump(rawjson, fl, indent = 4)
        return rawjson
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
Creates package config with specified name and, optionally, particular specified 
params (which are filled in with defaults where params are left unspecified)

returns pkg config id
"""
def create_pkg_config(name, queries = None):
    locsects = list(util.logsects[__file__])
    pkgc = empty_pkg_config(name)
    ret = {"val":None, "err":None}

    if queries:
        val_queries(queries)
        pkgc["queries"] = list(queries)
    else: 
        pkgc["queries"] = []

    pkgc["id"] = random.randint(pow(10, 10), pow(10, 11) - 1)

    return write_pkg_config(pkgc)
def remove_pkg_config(pkg_id):
    found = False
    
    if not path.exists("pers/pkg_configs.json"):
        return
    with open("pers/pkg_configs.json", "r+") as fl:
        raw = fl.read()
        if len(raw) == 0:
            return
        rawjson = json.loads(raw)
        for conf in rawjson:
            if conf["id"] == pkg_id:
                temp = conf
                rawjson.remove(conf)
                found = True
                break

        if not found:
            raise Exception(f"pkg config with id {pkg_id} not found")

        fl.truncate()
        json.dump(rawjson, fl)
        return rawjson
