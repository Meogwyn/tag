import asyncio
import aioconsole
"""
A websocat-like client for sending messages to the ipc server
"""

sendq = asyncio.Queue()

async def inp_task():
    while True:
        msg = await aioconsole.ainput()
        sendq.put_nowait(msg)
async def wtr_task(wtr):
    while True:
        msg = await sendq.get()
        wtr.write(int.to_bytes(len(msg), 4, "big") + msg.encode())
        await wtr.drain()
async def rdr_task(rdr):
    while True:
        msglen = await rdr.read(4)
        msg = await rdr.read(int.from_bytes(msglen, 'big'))
        print(f'{msg.decode()}')

async def main():
    rdr, wtr = await asyncio.open_connection('localhost', 15324)
    await asyncio.gather(wtr_task(wtr), rdr_task(rdr), inp_task())

asyncio.run(main())
