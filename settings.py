import sqlite3

con = sqlite3.connect("database.db", check_same_thread=False)
cursor = con.cursor()

cursor.execute(
    "CREATE TABLE IF NOT EXISTS users (id TEXT, cash INTEGER, start BOOLEAN, eday BOOLEAN, ref TEXT, promo BOOLEAN, "
    "get_promo BOOLEAN, msg_count INTEGER, last INTEGER, ends TEXT)")
con.commit()
cursor.execute("ALTER TABLE users ADD COLUMN ends TEXT")
con.commit()