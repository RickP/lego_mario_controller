import asyncio
from bleak import BleakScanner

async def run():
    devices = await BleakScanner.discover()
    for d in devices:
        print(d.name)
        if d.name == "LEGO Mario":
          async with BleakClient(d.address) as client:
            svcs = await client.get_services()
            print("Services:", svcs)

loop = asyncio.get_event_loop()
loop.run_until_complete(run())