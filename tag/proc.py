"""
For the curious reader, 'proc' stands for 'procedure'

N.B. the output should be padded by spaces on either side if the output is to 
preserve the separation between words. E.G.:

    abc $1 def ----- <substitute $1 with "xd"> -------> abcxddef
    abc $1 def ----- <substitute $1 with " xd "> -------> abc xd def

all funcs don't every modify the args, instead creating copies and returning 
relevant stuff. 
"""
import util


procs = []

def test_proc():
    util.taglog("BOO!", 1)

"""
FINAL PROC MAP DEFINITION
"""
procs.append({"test_proc", test_proc})

def exec_proc(*args)
    pass
