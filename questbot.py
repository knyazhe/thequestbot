import json
import sqlite3
from bot.bot import Bot
from mytoken import token

bot = Bot(token=token())
con = sqlite3.connect("database.db", check_same_thread=False)
cursor = con.cursor()

cursor.execute(
    "CREATE TABLE IF NOT EXISTS users (id TEXT, cash INTEGER, start BOOLEAN, eday BOOLEAN, ref TEXT, promo BOOLEAN, get_promo BOOLEAN, msg_count INTEGER, last INTEGER)")
con.commit()

with open('live.txt', mode='r', encoding="utf_8") as f:
    text = f.read().splitlines()

def everydayBonus():
    cursor.execute("UPDATE users_cash SET eday = 1")
    con.commit()


def addCash(user_id, cash, start=False):
    cursor.execute("SELECT id FROM users WHERE id = ?", [user_id])
    result = cursor.fetchone()
    if result is None:
        if start:
            cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           [user_id, cash, 1, 1, None, 0, 0, 0, 0])
            print(f"LOG: Create id: {user_id}, cash: {cash}")
        else:
            cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           [user_id, cash, 0, 1, None, 0, 0, 0, 0])
            print(f"LOG: Create id: {user_id}, cash: {cash}")
    else:
        if start:
            cursor.execute("SELECT start FROM users WHERE id = ?", [user_id])
            result = cursor.fetchone()
            if not result[0]:
                cursor.execute(
                    "SELECT cash FROM users WHERE id = ?", [user_id])
                result = cursor.fetchone()
                cursor.execute("UPDATE users SET cash = ?, start = 1 WHERE id = ?",
                               [int(result[0]) + int(cash), user_id])
                print(f"LOG: Add id: {user_id}, cash: {result[0]} (+{cash})")
        else:
            cursor.execute("SELECT cash FROM users WHERE id = ?", [user_id])
            result = cursor.fetchone()
            cursor.execute("UPDATE users SET cash = ? WHERE id = ?", [
                int(result[0]) + int(cash), user_id])
            print(f"LOG: Add id: {user_id}, cash: {result[0]} (+{cash})")
    con.commit()


def sendEnd(ans, event):
    if "{" in text[ans]:
        bot.send_text(chat_id=event.data['from']['userId'],
                      text="Это конец квеста.\nЧтобы запустить его заново, просто нажмите на кнопку.",
                      inline_keyboard_markup="{}".format(json.dumps(
                          [[{"text": "🔄Заново", "callbackData": "repeat", "style": "primary"},
                            {"text": "🗂️В меню", "callbackData": "menu", "style": "primary"}]])))


def getRating(user_id):
    cursor.execute("SELECT * FROM users ORDER BY cash DESC LIMIT 10")
    result = cursor.fetchall()
    text = ""
    your = 10
    for i in range(len(result)):
        text += f"{i + 1}. @{result[i][0]} - {result[i][1]} монет\n"
        if result[i][0] == user_id:
            your = i
    text += f"\nВы на {your + 1} месте."
    return text


def repl(ans):
    # Форматирует текст
    per1 = False
    per2 = False
    per3 = False
    out = ""
    num = ""
    replic = ""
    buttons = []
    konc = ""
    numKonc = []
    nums = []
    counter = 0
    for i in text[int(ans)]:
        if i == "*" and not per2:
            out += "\n"
        elif i == "{":
            per3 = True
        elif i == "}":
            per3 = False
            numKonc.append(int(konc))
        elif i == "<":
            per1 = True
            out += "\n"
        elif i == ">":
            per1 = False
            per2 = True
        elif i == ";" and per2:
            per2 = False
            nums.append(int(num))
            buttons.append([{"text": f"{replic}", "callbackData": f"{int(num)}", "style": "primary"}])
            replic = ""
            num = ""
            counter = 0
        elif per1 is True:
            num += i
        elif per2 is True:
            counter += 1
            if counter >= 25 and i == " ":
                replic += "\n"
                counter = 0
            if i == "*":
                replic += "\n"
            else:
                replic += i
        elif per3 is True:
            konc += i
        else:
            out += i
    buttons.append([{"text": "🗂️ Меню", "callbackData": "nmenu", "style": "base"}])
    return out, str(json.dumps(buttons)), nums


def isEnd(ans):
    x = False
    for i in text[ans]:
        if i == "{":
            x = True
    if x:
        return True
    else:
        return False