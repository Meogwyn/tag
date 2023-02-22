"""
Connects to localhost:15324 over tcp and sends commands every seconds
and prints any incoming responses
"""

import asyncio

msg = "{\"type\":\"ping\"}".encode()

async def wtr_task(wtr):
    while True:
        wtr.write(int.to_bytes(len(msg), 4, "big") + msg)
        print(f"raw send:{int.to_bytes(len(msg), 4, 'big') + msg}")
        await wtr.drain()
        await asyncio.sleep(1)
async def rdr_task(rdr):
    while True:
        msglen = await rdr.read(4)
        msg = await rdr.read(int.from_bytes(msglen, 'big'))
        print(f'incoming msg: {msg.decode()}')

async def main():
    rdr, wtr = await asyncio.open_connection('localhost', 15324)
    await asyncio.gather(wtr_task(wtr), rdr_task(rdr))

asyncio.run(main())
