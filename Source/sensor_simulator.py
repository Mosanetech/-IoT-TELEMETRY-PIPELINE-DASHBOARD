import asyncio
import random
import time
import yaml

from proto import telemetry_pb2


HOST = '127.0.0.1'
PORT = 8888


async def simulate_sensor(sensor):
    while True:
        try:
            reader, writer = await asyncio.open_connection(HOST, PORT)

            while True:
                reading = telemetry_pb2.SensorReading(
                    sensor_id=sensor['id'],
                    temperature=random.uniform(20, 35),
                    humidity=random.uniform(40, 90),
                    soil_moisture=random.uniform(20, 80),
                    light=random.uniform(100, 1000),
                    timestamp=int(time.time())
                )

                writer.write(reading.SerializeToString())
                await writer.drain()

                print(f"Sent reading from {sensor['id']}")

                await asyncio.sleep(sensor['interval'])

        except Exception as e:
            print(e)
            await asyncio.sleep(5)


async def main():
    with open('config/sensors.yaml', 'r') as f:
        config = yaml.safe_load(f)

    tasks = []

    for sensor in config['sensors']:
        tasks.append(simulate_sensor(sensor))

    await asyncio.gather(*tasks)


asyncio.run(main())