import asyncio
from tag import tag_prot
from tag import globs
from tag import util

"""
Some general comments on the server:

if the TAG_CLIENT_AGNOSTIC env var is set to false, the lifecycle of the server
(and tag in general) looks like this:

1. General stdby, waiting for client to connect.
2. Client connected, receiving commands and possibly eventually running an op.
3. Client disconnected, pause opertion until client reconnects.

The only difference with TAG_CLIENT_AGNOSTIC is that once a client starts an
extraction, it doesn't pause if a client disconnects, potentially allowing for
multiple clients to connect/disconnect as they please.


the ipc_serv struct is essentially the manager of read/write messages, capable
of sending and receiving messages. Sending messages is fairly straightforward
implementation-wise. Receiving is a bit more complex - messages are read in
the following format:

<msglen - 4 byte integer, big endian, unsigned><msg - JSON, msglen bytes long. UTF-8.>

If the connection dies mid-message, the message is discarded. Received messages
are pushed directly into the parsing queue (defined in tag_prot.py).
"""

util.taglog_add_file_sects(__file__, ["IPC_SERV"])
ipc_serv = None 

"""
Sends msg, which should be in the form of a string. Send format is the same as
the receive format (described above)
"""
def ipc_send(msg):
    ipc_serv.ipc_sendq.put_nowait(msg)

"""
Converts dict to string before sending
"""
def ipc_send_dict(msg):
    ipc_serv.ipc_sendq.put_nowait(str(msg))

"""
called on client connect, alters global ipc_serv instance
"""
def client_con_cb(reader, writer):
    ipc_serv.con_cb(reader, writer)

async def ipc_serv_task():
    global ipc_serv
    ipc_serv = ipc_serv_t()
    await ipc_serv.serve()
class ipc_serv_t():
    stat_disc = 0
    stat_conn = 1
    # run once from main
    def __init__(self, *args, **kargs):
        self.server = None
        self.rdr_tsk = None
        self.wtr_tsk = None
        self.status = ipc_serv_t.stat_disc
        self.ipc_sendq = asyncio.Queue()

    """
    receives a message of msglen bytes from reader and returns string 
    """
    async def recv_msg(msglen, reader):
        msg = await reader.read(msglen)
        return msg.decode()
    async def rdr_fnc(self, reader):
        locsects = list(util.logsects[__file__])
        locsects.append("RDR_FNC")
        util.taglog("reader started", 5000, locsects)
        try:
            while True:
                msglen = int.from_bytes(await reader.read(4), 'big')
                msg = await ipc_serv_t.recv_msg(msglen, reader)
                if msg == "":
                    break
                util.taglog(f"raw received message: {msg}", 5000, locsects)
                tag_prot.push_parseq_str(msg)
        except ConnectionResetError:
            pass
        except asyncio.CancelledError:
            pass
        self.wtr_tsk.cancel()
        util.taglog("reader exited", 5000, locsects)
        return
    async def wtr_fnc(self, writer):
        locsects = list(util.logsects[__file__])
        locsects.append("WTR_FNC")
        util.taglog("writer started", 5000, locsects)
        try:
            while True:
                msg = await self.ipc_sendq.get()
                msg = int.to_bytes(len(msg), 4, 'big') + msg.encode()
                util.taglog(f"raw message about to be sent: {msg}", 5000, locsects)
                writer.write(msg)
                await writer.drain()
        except ConnectionResetError:
            pass
        except asyncio.CancelledError:
            pass
        writer.close()
        util.taglog("writer exited", 5000, locsects)
        return

    async def serve(self):
        self.server = await asyncio.start_server(client_con_cb, 
                                                 globs.Globs["tcp_host"], 
                                                 globs.Globs["tcp_port"])
        async with self.server as server:
            util.taglog(f"started ipc server on '{globs.Globs['tcp_host']}:{globs.Globs['tcp_port']}'", 1000, util.logsects[__file__])
            await server.serve_forever()

    """
    disconnect any connected clients... presumably
    """
    async def shutdown(self):
        self.wtr_tsk.cancel()
        self.rdr_tsk.cancel()

    def con_cb(self, reader, writer):
        self.rdr_tsk = asyncio.create_task(self.rdr_fnc(reader))
        self.wtr_tsk = asyncio.create_task(self.wtr_fnc(writer))
        self.status = ipc_serv_t.stat_conn
