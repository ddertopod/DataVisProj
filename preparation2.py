import psycopg2
from CONFIG import Config
try:
    conn = psycopg2.connect(database = Config.DATABASE,
                                  user = Config.USER,
                                  password = Config.PASSWORD,
                                  host = Config.HOST)
    cursor = conn.cursor()
    sql = 'create table messages(message_id numeric, track_id numeric, terminal_id text, lat double precision, lon double precision, timestamp integer, speed integer, course integer, voltage real, motion integer, alt real, source text, ignition integer, odometer integer, satellites integer, gsmlevel integer, sensors json, externals json, outputs json, can_data json, temperature json, created timestamp without time zone);'
    cursor.execute(sql)
    conn.commit()
except Exception as e:
    print(f"Ошибка при работе с PostgreSQL: {e}")

cursor.close()
conn.close()