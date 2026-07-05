import sqlite3
import pandas as pd
from datetime import datetime
import os
DB_PATH = os.path.join(os.path.dirname(__file__), 'sensor_data.db')

CREATE_SQL = '''
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rain_24h REAL NOT NULL,
    rain_72h REAL NOT NULL,
    rhum REAL NOT NULL,
    drainage_score REAL NOT NULL,
    elevation_score REAL NOT NULL,
    actual_flood INTEGER,
    recorded_at TEXT NOT NULL DEFAULT (datetime('now')),
    source TEXT NOT NULL DEFAULT 'iot'
)
'''

_db_initialized = False


def _ensure_db():
    global _db_initialized
    if _db_initialized:
        return
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_SQL)
    conn.commit()
    conn.close()
    _db_initialized = True


def get_connection():
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def insert_reading(data: dict) -> int:
    conn = get_connection()
    cursor = conn.execute('''
        INSERT INTO sensor_readings (rain_24h, rain_72h, rhum, drainage_score, elevation_score, source)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        float(data['rain_24h']),
        float(data['rain_72h']),
        float(data['rhum']),
        float(data['drainage_score']),
        float(data['elevation_score']),
        data.get('source', 'iot')
    ))
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_all_readings() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query('SELECT * FROM sensor_readings ORDER BY recorded_at', conn)
    conn.close()
    return df


def get_historical_data() -> pd.DataFrame:
    csv_path = os.path.join(os.path.dirname(__file__), 'Lagos CSV')
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df['source'] = 'historical'
        return df
    return pd.DataFrame()


def get_reading_count() -> int:
    conn = get_connection()
    count = conn.execute('SELECT COUNT(*) FROM sensor_readings').fetchone()[0]
    conn.close()
    return count
