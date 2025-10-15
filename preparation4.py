import psycopg2
from CONFIG import Config
try:
    conn = psycopg2.connect(database = Config.DATABASE,
                                  user = Config.USER,
                                  password = Config.PASSWORD,
                                  host = Config.HOST)
    cursor = conn.cursor()
    sql = 'create table calibrating(id integer not null, deviceid_port text, calibrating_data json);'
    cursor.execute(sql)
    conn.commit()
except Exception as e:
    print(f"Ошибка при работе с PostgreSQL: {e}")

cursor.close()
conn.close()