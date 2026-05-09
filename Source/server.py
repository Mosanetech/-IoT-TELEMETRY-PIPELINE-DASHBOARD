import asyncio
from aiohttp import web
from aiohttp.web import Response
from google.protobuf.message import DecodeError

from proto import telemetry_pb2
from database import init_db, insert_reading, get_readings
from websocket_manager import register, unregister, broadcast

sensors = {}


async def tcp_sensor_handler(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Sensor connected: {addr}")

    while True:
        try:
            data = await reader.read(1024)

            if not data:
                break

            reading = telemetry_pb2.SensorReading()
            reading.ParseFromString(data)

            sensors[reading.sensor_id] = {
                "sensor_id": reading.sensor_id
            }

            await insert_reading(reading)

            payload = {
                "sensor_id": reading.sensor_id,
                "temperature": reading.temperature,
                "humidity": reading.humidity,
                "soil_moisture": reading.soil_moisture,
                "light": reading.light,
                "timestamp": reading.timestamp,
            }

            await broadcast(payload)

            print("Received:", payload)

        except DecodeError:
            print("Malformed protobuf received")

        except Exception as e:
            print(e)
            break

    writer.close()
    await writer.wait_closed()


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    await register(ws)

    async for msg in ws:
        pass

    await unregister(ws)

    return ws


async def list_sensors(request):
    return web.json_response(list(sensors.values()))


async def sensor_readings(request):
    sensor_id = request.match_info['id']
    rows = await get_readings(sensor_id)

    data = []

    for row in rows:
        data.append({
            "id": row[0],
            "sensor_id": row[1],
            "temperature": row[2],
            "humidity": row[3],
            "soil_moisture": row[4],
            "light": row[5],
            "timestamp": row[6],
        })

    accept = request.headers.get('Accept', 'application/json')

    if 'application/xml' in accept:
        xml = '<readings>'

        for r in data:
            xml += f"""
            <reading>
                <sensor_id>{r['sensor_id']}</sensor_id>
                <temperature>{r['temperature']}</temperature>
            </reading>
            """

        xml += '</readings>'

        return Response(text=xml, content_type='application/xml')

    if 'application/x-yaml' in accept:
        import yaml

        return Response(
            text=yaml.dump(data),
            content_type='application/x-yaml'
        )

    return web.json_response(data)


async def add_sensor(request):
    data = await request.json()

    sensors[data['id']] = data

    response = web.json_response({
        "message": "Sensor registered"
    })

    response.set_cookie(
        "session_id",
        "net322-session"
    )

    return response


async def delete_sensor(request):
    sensor_id = request.match_info['id']

    if sensor_id in sensors:
        del sensors[sensor_id]

    return web.json_response({
        "message": "Sensor removed"
    })

async def dashboard(request):
    return web.FileResponse('static/index.html')

async def start_servers():
    await init_db()

    tcp_server = await asyncio.start_server(
        tcp_sensor_handler,
        '127.0.0.1',
        8888
    )

    print("TCP Sensor Server running on port 8888")

    app = web.Application()

    app.router.add_get('/sensors', list_sensors)
    app.router.add_get('/sensors/{id}/readings', sensor_readings)
    app.router.add_post('/sensors', add_sensor)
    app.router.add_delete('/sensors/{id}', delete_sensor)

    app.router.add_get('/live', websocket_handler)

    app.router.add_get('/', dashboard)

    app.router.add_static(
        '/static/',
        path='static',
        name='static'
    )

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        '127.0.0.1',
        8080
    )

    await site.start()

    print("Dashboard running at:")
    print("http://127.0.0.1:8080")

    async with tcp_server:
        await tcp_server.serve_forever()


asyncio.run(start_servers())