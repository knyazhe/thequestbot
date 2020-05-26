import json
import traceback
import sqlite3
from random import randint, choice
from bot.bot import Bot
from bot.handler import MessageHandler, BotButtonCommandHandler, StartCommandHandler

TOKEN = "TOKEN"
bot = Bot(token=TOKEN)

con = sqlite3.connect("database.db", check_same_thread=False)
cursor = con.cursor()

cursor.execute(
    "CREATE TABLE IF NOT EXISTS users (id TEXT, cash INTEGER, start BOOLEAN, eday BOOLEAN, ref TEXT, promo BOOLEAN, get_promo BOOLEAN, msg_count INTEGER, last INTEGER)")
con.commit()

symb = "0123456789abcdefghijklmnopqrstuvwxyz"

with open('live.txt', mode='r', encoding="utf_8") as f:
    text = f.read().splitlines()


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


def start_cb(bot, event):
    addCash(event.from_chat, 200, True)
    bot.send_text(chat_id=event.from_chat,
                  text=f"Добро пожаловать, {event.data['from']['firstName']}!\nВы находитесь в 🗂️ Меню",
                  inline_keyboard_markup="{}".format(json.dumps(
                      [[{"text": "📚 Квесты", "callbackData": "quests", "style": "primary"}],
                       [{"text": "📊 Рейтинг", "callbackData": "rate", "style": "primary"}],
                       [{"text": "💰 Кошелёк", "callbackData": "money", "style": "primary"},
                        {"text": "ℹ ️Инфо", "callbackData": "info", "style": "primary"}]])))


def isEnd(ans):
    x = False
    for i in text[ans]:
        if i == "{":
            x = True
    if x:
        return True
    else:
        return False


def answer_cb(bot, event):
    try:
        addCash(event.data['from']['userId'], 200, True)
        if str(event.type) == 'EventType.NEW_MESSAGE':
            print(event.data['from']['userId'], event.data['text'])
        else:
            print(event.data['from']['userId'], event.data['callbackData'])

        if str(event.type) == 'EventType.NEW_MESSAGE':
            cursor.execute("SELECT promo FROM users WHERE id = ?", [event.data['from']['userId']])
            promo = cursor.fetchone()[0]
            event.data['text'] = event.data['text'].lower()
            if promo:
                cursor.execute("SELECT ref FROM users WHERE ref = ?", [event.data['text'].lower()])
                ref = cursor.fetchone()
                cursor.execute("SELECT get_promo FROM users WHERE id = ?", [event.data['from']['userId']])
                get_promo = cursor.fetchone()[0]
                if get_promo:
                    bot.send_text(chat_id=event.data['from']['userId'],
                                  text="Вы уже вводили промокод",
                                  inline_keyboard_markup="{}".format(json.dumps(
                                      [[{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))
                    cursor.execute("UPDATE users SET promo = 0 WHERE id = ?", [event.data['from']['userId']])
                elif ref:
                    cursor.execute("SELECT ref FROM users WHERE id = ?", [event.data['from']['userId']])
                    self_ref = cursor.fetchone()[0]
                    if ref[0] == self_ref:
                        bot.send_text(chat_id=event.data['from']['userId'],
                                      text="Не стоит хитрить :)",
                                      inline_keyboard_markup="{}".format(json.dumps(
                                          [[{"text": "Ещё раз", "callbackData": "promo", "style": "primary"}],
                                           [{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))
                        cursor.execute("UPDATE users SET promo = 0 WHERE id = ?", [event.data['from']['userId']])

                    else:
                        cursor.execute("UPDATE users SET get_promo = 1 WHERE id = ?", [event.data['from']['userId']])
                        cursor.execute("SELECT cash FROM users WHERE ref = ?", [event.data['text']])
                        cash = cursor.fetchone()[0]
                        cursor.execute("UPDATE users SET promo = 0 WHERE id = ?", [event.data['from']['userId']])
                        cursor.execute("UPDATE users SET cash = ? WHERE ref = ?", [cash + 30, event.data['text']])
                        cursor.execute("SELECT cash FROM users WHERE id = ?", [event.data['from']['userId']])
                        cash = cursor.fetchone()[0]
                        cursor.execute("UPDATE users SET cash = ? WHERE id = ?",
                                       [cash + 30, event.data['from']['userId']])
                        bot.send_text(chat_id=event.data['from']['userId'],
                                      text="Такой промокод есть! Вам зачислено 30 монет",
                                      inline_keyboard_markup="{}".format(json.dumps(
                                          [[{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))
                else:
                    bot.send_text(chat_id=event.data['from']['userId'],
                                  text="Такого промокода нет :(",
                                  inline_keyboard_markup="{}".format(json.dumps(
                                      [[{"text": "Ещё раз", "callbackData": "promo", "style": "primary"}],
                                       [{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))
                    cursor.execute("UPDATE users SET promo = 0 WHERE id = ?", [event.data['from']['userId']])
            else:
                start_cb(bot, event)
            con.commit()
        else:
            bot.answer_callback_query(
                query_id=event.data['queryId'],
                text="")
            if event.data['callbackData'] == "quest":
                cursor.execute("SELECT last FROM users WHERE id = ?", [event.data['from']['userId']])
                last = cursor.fetchone()[0]
                bot.send_text(chat_id=event.data['from']['userId'],
                              text=repl(last)[0],
                              inline_keyboard_markup=repl(last)[1])

            elif event.data['callbackData'] == "repeat":
                bot.send_text(chat_id=event.data['from']['userId'],
                              text=repl(0)[0],
                              inline_keyboard_markup=repl(0)[1])
                cursor.execute("UPDATE users SET last = ? WHERE id = ?", [0, event.data['from']['userId']])

            elif event.data['callbackData'] == "bonus":
                cursor.execute("SELECT eday FROM users WHERE id =?", [event.data['from']['userId']])
                result = cursor.fetchone()
                if result[0]:
                    bmoney = randint(5, 10)
                    addCash(event.data['from']['userId'], bmoney, False)
                    bot.edit_text(chat_id=event.data['from']['userId'],
                                  msg_id=event.data['message']['msgId'],
                                  text=f"Ваш бонус: {bmoney}.\nВозвращайтесь завтра!",
                                  inline_keyboard_markup="{}".format(json.dumps(
                                      [[{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))
                    cursor.execute("UPDATE users SET eday = 0 WHERE id = ?", [
                        event.data['from']['userId']])
                else:
                    bot.edit_text(chat_id=event.data['from']['userId'],
                                  msg_id=event.data['message']['msgId'],
                                  text="Возвращайтесь завтра!",
                                  inline_keyboard_markup="{}".format(json.dumps(
                                      [[{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))

            elif event.data['callbackData'] == "rate":
                bot.edit_text(chat_id=event.data['from']['userId'],
                              msg_id=event.data['message']['msgId'],
                              text=getRating(event.data['from']['userId']),
                              inline_keyboard_markup="{}".format(json.dumps(
                                  [[{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))

            elif event.data['callbackData'] == "menu":
                bot.edit_text(chat_id=event.data['from']['userId'],
                              msg_id=event.data['message']['msgId'],
                              text=f"Добро пожаловать, {event.data['from']['firstName']}!\nВы находитесь в 🗂️Меню",
                              inline_keyboard_markup="{}".format(json.dumps(
                                  [[{"text": "📚 Квесты", "callbackData": "quests", "style": "primary"}],
                                   [{"text": "📊 Рейтинг", "callbackData": "rate",
                                     "style": "primary"}],
                                   [{"text": "💰 Кошелёк", "callbackData": "money", "style": "primary"},
                                    {"text": "ℹ ️Инфо", "callbackData": "info", "style": "primary"}]])))

            elif event.data['callbackData'] == "nmenu":
                bot.send_text(chat_id=event.data['from']['userId'],
                              text=f"Добро пожаловать, {event.data['from']['firstName']}!\nВы находитесь в 🗂️Меню",
                              inline_keyboard_markup="{}".format(json.dumps(
                                  [[{"text": "📚 Квесты", "callbackData": "quests", "style": "primary"}],
                                   [{"text": "📊 Рейтинг", "callbackData": "rate",
                                     "style": "primary"}],
                                   [{"text": "💰 Кошелёк", "callbackData": "money", "style": "primary"},
                                    {"text": "ℹ ️Инфо", "callbackData": "info", "style": "primary"}]])))

            elif event.data['callbackData'] == "ref":
                bot.edit_text(chat_id=event.data['from']['userId'],
                              msg_id=event.data['message']['msgId'],
                              text=f"Приглашайте друзей и получайте за них монеты",
                              inline_keyboard_markup="{}".format(json.dumps(
                                  [[{"text": "Мой код", "callbackData": "get-ref", "style": "primary"},
                                    {"text": "Ввести код", "callbackData": "promo", "style": "primary"}],
                                   [{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))

            elif event.data['callbackData'] == "get-ref":
                cursor.execute("SELECT ref FROM users WHERE id = ?", [event.data['from']['userId']])
                result = cursor.fetchone()
                if result[0] is None:
                    cursor.execute("SELECT ref FROM users")
                    result = cursor.fetchall()
                    code = ""
                    for i in range(4):
                        code += choice(symb)
                    while code in result:
                        code = ""
                        for i in range(4):
                            code += choice(symb)
                    cursor.execute("UPDATE users SET ref = ? WHERE id = ?", [code, event.data['from']['userId']])
                    bot.edit_text(chat_id=event.data['from']['userId'],
                                  msg_id=event.data['message']['msgId'],
                                  text=f"Ваш код: {code}",
                                  inline_keyboard_markup="{}".format(json.dumps(
                                      [[{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))

                else:
                    cursor.execute("SELECT ref FROM users WHERE id = ?", [event.data['from']['userId']])
                    code = cursor.fetchone()[0]
                    bot.edit_text(chat_id=event.data['from']['userId'],
                                  msg_id=event.data['message']['msgId'],
                                  text=f"Ваш код: {code}",
                                  inline_keyboard_markup="{}".format(json.dumps(
                                      [[{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))
                con.commit()

            elif event.data['callbackData'] == "promo":
                cursor.execute("UPDATE users SET promo = 1 WHERE id = ?", [event.data['from']['userId']])
                bot.edit_text(chat_id=event.data['from']['userId'],
                              msg_id=event.data['message']['msgId'],
                              text=f"Отправьте код сообщением.",
                              inline_keyboard_markup="{}".format(json.dumps(
                                  [[{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))
                con.commit()

            elif event.data['callbackData'] == "quests":
                bot.edit_text(chat_id=event.data['from']['userId'],
                              msg_id=event.data['message']['msgId'],
                              text=f"{event.data['from']['firstName']}, выбирайте то, что душе угодно",
                              inline_keyboard_markup="{}".format(json.dumps(
                                  [[{"text": "Живое", "callbackData": "quest", "style": "primary"}],
                                   [{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))

            elif event.data['callbackData'] == "money":
                cursor.execute("SELECT cash FROM users WHERE id = ?", [event.data['from']['userId']])
                money = cursor.fetchone()[0]
                bot.edit_text(chat_id=event.data['from']['userId'],
                              msg_id=event.data['message']['msgId'],
                              text=f"{event.data['from']['firstName']}, это Ваш кошелёк.\nВаш баланс: {money}",
                              inline_keyboard_markup="{}".format(json.dumps(
                                  [[{"text": "💼 Реф. система", "callbackData": "ref", "style": "base"},
                                    {"text": "💸 Ежедневный бонус", "callbackData": "bonus", "style": "base"}],
                                   [{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))

            elif event.data['callbackData'] == "info":
                bot.edit_text(chat_id=event.data['from']['userId'],
                              msg_id=event.data['message']['msgId'],
                              text="ℹ ️Информация об авторах и боте",
                              inline_keyboard_markup="{}".format(json.dumps(
                                  [[{"text": "🤖 О боте", "callbackData": "aboutbot", "style": "base"},
                                    {"text": "👥 Об \nавторах", "callbackData": "authors", "style": "base"}],
                                   [{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))

            elif event.data['callbackData'] == "authors":
                bot.edit_text(chat_id=event.data['from']['userId'],
                              msg_id=event.data['message']['msgId'],
                              text='''Авторы:
            👨‍💻 Олег - Автор идеи; Программист.
            VK/ICQ: @oleg.json
                              
            📝 Анна - Писатель.
            Inst: anna_sulimova2004
            ICQ: @diagon_alley''',
                              inline_keyboard_markup="{}".format(json.dumps(
                                  [[{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))

            elif event.data['callbackData'] == "aboutbot":
                bot.edit_text(chat_id=event.data['from']['userId'],
                              msg_id=event.data['message']['msgId'],
                              text="Данный бот можеть поведать Вам истории с той концовкой, к которой Вы сами "
                                   "пришли\n\nПо всем вопросам: thequestbot@gmail.com",
                              inline_keyboard_markup="{}".format(json.dumps(
                                  [[{"text": "🗂️ Меню", "callbackData": "menu", "style": "base"}]])))

            elif event.data['callbackData'] == "nalog":
                cursor.execute("SELECT cash FROM users WHERE id = ?", [event.data['from']['userId']])
                cash = int(cursor.fetchone()[0])
                if cash - 10 >= 0:
                    cursor.execute("UPDATE users SET cash = ? WHERE id = ?", [cash - 10, event.data['from']['userId']])
                    bot.send_text(chat_id=event.data['from']['userId'],
                                  text="✅ Оплата прошла успешно")
                    cursor.execute("UPDATE users SET msg_count = 0 WHERE id = ?", [event.data['from']['userId']])
                    cursor.execute("SELECT last FROM users WHERE id = ?", [event.data['from']['userId']])
                    last = cursor.fetchone()[0]
                    bot.send_text(chat_id=event.data['from']['userId'],
                                  text=repl(last)[0],
                                  inline_keyboard_markup=repl(last)[1])
                else:
                    if (cash - 10) * -1 < 5:
                        t = "монеты"
                    else:
                        t = "монет"
                    bot.send_text(chat_id=event.data['from']['userId'],
                                  text=f"❌ Не хватает {(cash - 10) * -1} {t}.\nЗаработать можно в разделе 💰Кошелёк",
                                  inline_keyboard_markup="{}".format(json.dumps(
                                      [[{"text": "🗂️Меню", "callbackData": "menu", "style": "base"}]])))

            else:
                if not isEnd(int(event.data['callbackData'])):
                    if len(repl(int(event.data['callbackData']))[1]) > 4:
                        cursor.execute("SELECT msg_count FROM users WHERE id = ?", [event.data['from']['userId']])
                        count = cursor.fetchone()[0]
                        cursor.execute("SELECT last FROM users WHERE id = ?", [event.data['from']['userId']])
                        last = cursor.fetchone()[0]
                        if int(count) >= 5:
                            bot.send_text(chat_id=event.data['from']['userId'],
                                          text="Для продолжения нужно заплатить 10 монет",
                                          inline_keyboard_markup="{}".format(json.dumps(
                                              [[{"text": "💰 Заплатить", "callbackData": "nalog", "style": "primary"},
                                                {"text": "🗂️ Меню", "callbackData": "menu", "style": "primary"}]])))
                        elif int(event.data['callbackData']) in repl(last)[2]:
                            cursor.execute("UPDATE users SET msg_count = ? WHERE id = ?",
                                           [int(count) + 1, event.data['from']['userId']])
                            bot.send_text(chat_id=event.data['from']['userId'],
                                          text=repl(int(event.data['callbackData']))[0],
                                          inline_keyboard_markup=repl(int(event.data['callbackData']))[1])
                            for i in event.data['message']['parts'][0]['payload']:
                                if i[0]['callbackData'] == event.data['callbackData']:
                                    replica = i[0]['text']
                            bot.edit_text(chat_id=event.data['from']['userId'],
                                          msg_id=event.data['message']['msgId'],
                                          text=repl(int(last))[0]+f"===== {replica} =====")
                            cursor.execute("UPDATE users SET last = ? WHERE id = ?",
                                           [int(event.data['callbackData']), event.data['from']['userId']])
                        else:
                            cursor.execute("SELECT last FROM users WHERE id = ?", [event.data['from']['userId']])
                            last = int(cursor.fetchone()[0])
                            bot.send_text(chat_id=event.data['from']['userId'],
                                          text="Не жульничайте! Не нажимайте на кнопки из других сообщений.")
                            bot.send_text(chat_id=event.data['from']['userId'],
                                          text=repl(last)[0],
                                          inline_keyboard_markup=repl(last)[1])
                    else:
                        bot.send_text(chat_id=event.data['from']['userId'],
                                      text=repl(int(event.data['callbackData']))[0])
                        sendEnd(int(event.data['callbackData']), event)
                else:
                    bot.send_text(chat_id=event.data['from']['userId'],
                                  text=repl(int(event.data['callbackData']))[0])
                    cursor.execute("UPDATE users SET msg_count = 0 WHERE id = ?", [event.data['from']['userId']])
                    cursor.execute("UPDATE users SET last = ? WHERE id = ?", [int(event.data['callbackData']), event.data['from']['userId']])
                    bot.send_text(chat_id=event.data['from']['userId'],
                                  text="Это конец квеста.\nЧтобы запустить его заново, просто нажмите на кнопку.",
                                  inline_keyboard_markup="{}".format(json.dumps(
                                      [[{"text": "🔄 Заново", "callbackData": "repeat", "style": "primary"},
                                        {"text": "🗂️ Меню", "callbackData": "menu", "style": "primary"}]])))
            con.commit()
    except Exception as e:
        print(traceback.format_exc())


bot.dispatcher.add_handler(BotButtonCommandHandler(callback=answer_cb))
bot.dispatcher.add_handler(StartCommandHandler(callback=start_cb))
bot.dispatcher.add_handler(MessageHandler(callback=answer_cb))
bot.start_polling()
bot.idle()