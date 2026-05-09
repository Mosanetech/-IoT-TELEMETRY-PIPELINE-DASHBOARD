import aiosqlite

DB_PATH = "data/telemetry.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT,
                temperature REAL,
                humidity REAL,
                soil_moisture REAL,
                light REAL,
                timestamp INTEGER
            )
            """
        )

        await db.commit()


async def insert_reading(reading):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO readings
            (sensor_id, temperature, humidity, soil_moisture, light, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                reading.sensor_id,
                reading.temperature,
                reading.humidity,
                reading.soil_moisture,
                reading.light,
                reading.timestamp,
            ),
        )

        await db.commit()


async def get_readings(sensor_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT * FROM readings WHERE sensor_id=?",
            (sensor_id,),
        )

        rows = await cursor.fetchall()
        return rows