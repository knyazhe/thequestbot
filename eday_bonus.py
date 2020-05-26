import time
import sqlite3

con = sqlite3.connect("database.db", check_same_thread=False)
cursor = con.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users_cash (id TEXT, cash INTEGER, start BOOLEAN, eday BOOLEAN, ref TEXT)""")
con.commit()

while True:
    now_time = time.localtime(time.time())
    if now_time.tm_hour == 23 and now_time.tm_min == 40 and now_time.tm_sec == 0:
        cursor.execute("UPDATE users_cash SET eday = 1")
        con.commit()