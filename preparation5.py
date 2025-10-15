import psycopg2
from pathlib import Path
from CONFIG import Config

BASE_DIR = Path(__file__).resolve().parent
csv_path = BASE_DIR / "data" / "calib2.csv" 
try:
    conn = psycopg2.connect(database = Config.DATABASE,
                                  user = Config.USER,
                                  password = Config.PASSWORD,
                                  host = Config.HOST)
    cursor = conn.cursor()
    with open(csv_path, 'r') as f:
        cursor.copy_expert(f'''copy calibrating from STDIN delimiter ',' csv header''', f)
    conn.commit()
except Exception as e:
    print(f"Ошибка при работе с PostgreSQL: {e}")

cursor.close()
conn.close()