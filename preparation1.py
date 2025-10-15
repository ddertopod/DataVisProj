import psycopg2
from CONFIG import Config
try:
    conn = psycopg2.connect(database = Config.FIRSTBASE,
                                  user = Config.USER,
                                  password = Config.PASSWORD,
                                  host = Config.HOST)
    cursor = conn.cursor()
    conn.autocommit = True
    sql = 'create database bigdata'
    cursor.execute(sql)
except Exception as e:
    print(f"Ошибка при работе с PostgreSQL: {e}")

cursor.close()
conn.close()