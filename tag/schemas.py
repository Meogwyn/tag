"""
oai stuff occording to oai docs:
https://platform.openai.com/docs/api-reference/completions/create
"""
pkg_config_schema = {
    "additionalProperties": False,
    "type":"object",
    "properties": {
        "name": {"type":"string"},
        "id": {
            "type":"integer",
            "maximum": pow(10, 10) - 1,
            "minimum": pow(10, 9),
        },
        "output_dir": {"type": "string"},
        "overwrite": {"type": "boolean"},
        "ideas": {
            "type":"array",
            "items": {
                "type": "string",
            }
        },
        "oai_config_gen": { #TODO: reference single schema for oai_config_gen and oai_config below
            "type": "object", 
            "properties": { # note lack of 'prompt'. underrides 'queries'
                "model": {"type": "string"},
                "max_tokens": {"type": "integer"},
                "temperature": {"type": "number"},
                "top_p": {"type": "number"},
                "n": {"type": "integer"},
                "stream": {"type": "boolean"},
                "logprobs": {
                    "type": "integer", 
                    "maximum": 5
                },
                "stop": {"type": ["string", "array"]},
                "presence_penalty": {"type": "number"},
                "frequency_penalty": {"type": "number"},
                "best_of": {"type": "integer"},
                "logit_bias": {"type": "object"},
                "user": {"type": "string"},
            },
        },
        "queries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"} ,
                    "out_header": {"type":"string"}, #header to place at top of output
#                    "inp_cb_gen": {"type": "string"},
                    "inp_cb_map": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "idx": {"type":"integer"},
                            "cb_name": {"type": "string"}
                        },
                        "required": ["idx", "cb_name"]
                    },
                    "out_cb": {"type": "string"},


                    "oai_config": { #overrides oai_config_gen up above
                        "type": "object", 
                        "properties": {
                            "model": {"type": "string"},
                            "prompt": {"type": ["string", "array"]},
                            "max_tokens": {"type": "integer"},
                            "temperature": {"type": "number"},
                            "top_p": {"type": "number"},
                            "n": {"type": "integer"},
                            "stream": {"type": "boolean"},
                            "logprobs": {
                                "type": "integer", 
                                "maximum": 5
                            },
                            "stop": {"type": ["string", "array"]},
                            "presence_penalty": {"type": "number"},
                            "frequency_penalty": {"type": "number"},
                            "best_of": {"type": "integer"},
                            "logit_bias": {"type": "object"},
                            "user": {"type": "string"},
                        },
                        "required": ["model"]
                    }
                },
                "required": ["prompt", "out_header", "oai_config"]
            }
        }
    },
    "required": [
            "name",
            "id",
            "ideas",
            "queries",
            "output_dir"
    ]
}

