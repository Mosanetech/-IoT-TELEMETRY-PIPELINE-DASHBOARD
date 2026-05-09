import json

clients = set()


async def register(ws):
    clients.add(ws)


async def unregister(ws):
    clients.remove(ws)


async def broadcast(data):
    disconnected = set()

    for ws in clients:
        try:
            await ws.send_json(data)
        except:
            disconnected.add(ws)

    for ws in disconnected:
        clients.remove(ws)