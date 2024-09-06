from telebot.async_telebot import AsyncTeleBot
import asyncio
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, Message
from datetime import datetime, timedelta
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json
from image_const import *
from text_const import *

class Vahta:
    def __init__(self,date, item):
        self.date = date
        self.time = ""
        self.vahter = []
        self.item = item

    def to_serializable(self):
        return {"date":self.date,"time":self.time,"vahter":self.vahter, "item":self.item}


bot = AsyncTeleBot("7515847250:AAH1FW-pEKWcgl4J7SZX4ZDCVQdxQUQzhJo")

def write_file(chat_id, write_file):
    with open(f"jsons/{chat_id}.json","w") as file:
        json.dump(write_file, file)

def read_file(chat_id):
    if os.path.getsize(f"jsons/{chat_id}.json"):
        with open(f"jsons/{chat_id}.json") as file:
            data = json.load(file)
            return data
    else:
        return {}

def back_to_menu_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Вернуться в меню", callback_data="back_admin"))
    return markup

def gen_users_markup(chat_id):
    data = read_file(chat_id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Вернуться в меню", callback_data="back_admin"))
    buttons = []
    for username in data["users"]:
        buttons.append(InlineKeyboardButton(f"{username}",
                                            callback_data=f"vahta_user:{username}"))
    markup.add(*buttons, row_width=4)
    return markup

def gen_admin_vahta_day_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Вернуться в меню", callback_data="back_admin"))
    buttons = []
    today = datetime.today()
    for day_index in range(31):
        date = (today + timedelta(day_index)).date()
        callback_data = f"{(today + timedelta(day_index)).date()}"
        date_text = f"{str(date.day).zfill(2)}.{str(date.month).zfill(2)}"
        buttons.append(InlineKeyboardButton(f"{date_text}",
                                            callback_data=f"admin_vahta_day:{callback_data}"))
    markup.add(*buttons, row_width=4)
    return markup



def gen_main_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Назначить вахту", callback_data="vahta_manage"),
               InlineKeyboardButton("Список вахт", callback_data="vahta_list"),
               InlineKeyboardButton("Отработанные вахты", callback_data="vahta_maded"))

    return markup

def gen_remove_markup(date,time):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    data = {"action":"remove","date":date,"time":time}
    json_string = json.dumps(data)
    markup.add(InlineKeyboardButton("❌", callback_data=json_string))

    return markup



@bot.callback_query_handler(func=lambda call: True)
async def callback_query(call: CallbackQuery):
    data_admins = read_file("admins")
    if str(call.from_user.id) not in data_admins["admins"]:
        return
    if "vahta_manage" in call.data:
        with open(VAHTA_IMG, 'rb') as photo:
            file = InputMediaPhoto(photo)
            file.caption = VAHTA_GEN_TEXT
            await bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.id, media=file, reply_markup=back_to_menu_markup())
            try:
                data = read_file(call.message.chat.id)
                data["writing"] = True
                data["time_writing"] = False
                write_file(call.message.chat.id,data)
            except FileNotFoundError:
                write_file(call.message.chat.id, {"writing":True, "time_writing":False, "users":[]})
    elif "vahta_user" in call.data:
        user = call.data.replace("vahta_user:", "")
        with open(MAIN_IMG, 'rb') as photo:
            file = InputMediaPhoto(photo)
            file.caption = f"{VAHTA_USER_SET}: {user}"
            data = read_file(call.message.chat.id)
            item = data["current_item"]
            current_vahta = data["current_vahta"]
            data[item][current_vahta]["vahter"].append(user)
            data["writing"] = False
            data["time_writing"] = False
            write_file(call.message.chat.id, data)
            await bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.id, media=file, reply_markup=gen_users_markup(call.message.chat.id))
    elif "admin_vahta_day" in call.data:
        date = call.data.replace("admin_vahta_day:", "")
        with open(MAIN_IMG, 'rb') as photo:
            file = InputMediaPhoto(photo)
            file.caption = VAHTA_TIME_TEXT
            data = read_file(call.message.chat.id)
            item = data["current_item"]
            try:
                vahta = Vahta(date, item).to_serializable()
                data[item].append(vahta)
            except:
                data[item] = []
                vahta = Vahta(date, item).to_serializable()
                data[item].append(vahta)
            data["current_vahta"] = data[item].index(vahta)
            data["time_writing"] = True
            write_file(call.message.chat.id, data)
            await bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.id, media=file, reply_markup=back_to_menu_markup())
    elif "back_admin" in call.data:
        data = read_file(call.message.chat.id)
        data["writing"] = False
        data["time_writing"] = False
        write_file(call.message.chat.id, data)
        with open(MAIN_IMG, 'rb') as photo:
            file = InputMediaPhoto(photo)
            file.caption = MAIN_TEXT
            await bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.id, media=file, reply_markup=gen_main_markup())
    elif "vahta_list" in call.data:
        with open(MAIN_IMG, 'rb') as photo:
            file = InputMediaPhoto(photo)
            data = read_file(call.message.chat.id)
            for item in data.keys():
                if "date" in f"{data[item]}":
                    today = datetime.today()
                    for every_vahta in data[item]:
                        if datetime.strptime(every_vahta['date'], "%Y-%m-%d") >= today:
                            vahta_text = (f"Вахта: {every_vahta['item']}\n"
                                          f"Дата: {every_vahta['date']}\n"
                                          f"Время: {every_vahta['time']}\n"
                                          f"Ответственные: {every_vahta['vahter']}")
                            await bot.send_message(chat_id=call.message.chat.id, text=vahta_text,
                                                reply_markup=gen_remove_markup(every_vahta['date'],every_vahta['time']))

    elif "remove" in call.data:
        vahta_data = json.loads(call.data)
        data = read_file(call.message.chat.id)
        for item in data.keys():
            if "date" in f"{data[item]}":
                for every_vahta in data[item]:
                    if every_vahta["date"] == vahta_data["date"] and every_vahta["time"] == vahta_data["time"]:
                        index = data[item].index(every_vahta)
                        data[item].pop(index)
                        write_file(call.message.chat.id, data)
        with open(MAIN_IMG, 'rb') as photo:
            file = InputMediaPhoto(photo)
            file.caption = MAIN_TEXT
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Вахта удалена", reply_markup=gen_main_markup())
    elif "vahta_maded" in call.data:
        data = read_file(call.message.chat.id)
        text = "Отработанные вахты: \n\n"
        for item in data.keys():
            vahters_count = {}
            if "date" in f"{data[item]}":
                today = datetime.today()
                for every_vahta in data[item]:
                    if datetime.strptime(every_vahta['date'], "%Y-%m-%d") <= today:
                        for vahter in every_vahta['vahter']:
                            if vahter in vahters_count.keys():
                                vahters_count[vahter] += 1
                            else:
                                vahters_count[vahter] = 1
                    for vahter,count in vahters_count.items():
                        text += f"{vahter}: {count}\n"
        with open(MAIN_IMG, 'rb') as photo:
            file = InputMediaPhoto(photo)
            file.caption = text
            await bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.id, media=file,
                                    reply_markup=gen_main_markup())




@bot.message_handler(commands=['startvahta'])
async def start(message):
    data_admins = read_file("admins")
    if str(message.from_user.id) not in data_admins["admins"]:
        return
    with open(MAIN_IMG, 'rb') as photo:
        await bot.send_photo(message.chat.id, photo, caption=MAIN_TEXT, reply_markup=gen_main_markup())


@bot.message_handler(commands=['addadmin'])
async def addadmin(message):
    if message.from_user.id == 1879647372:
        data = read_file("admins")
        data["admins"].append(message.text.split()[1])
        write_file("admins", data)


@bot.message_handler(commands=['adduser'])
async def adduser(message):
    data_admins = read_file("admins")
    data = read_file(message.chat.id)
    if str(message.from_user.id) in data_admins["admins"]:
        data["users"].append(message.text.split()[1])
        write_file(message.chat.id, data)


@bot.message_handler(content_types=['text'])
async def read_text(message: Message):
    data = read_file(message.chat.id)
    data_admins = read_file("admins")
    if str(message.from_user.id) not in data_admins["admins"]:
        return
    if data["time_writing"]  == True:
        item = data["current_item"]
        current_vahta = data["current_vahta"]
        data[item][current_vahta]["time"] = message.text
        write_file(message.chat.id, data)
        with open(VAHTA_DATES_IMG, 'rb') as photo:
            await bot.send_photo(message.chat.id, photo, caption=f"{VAHTA_TIMESET_TEXT} : {message.text}.\n{VAHTA_SET_USER}", reply_markup=gen_users_markup(message.chat.id))
    elif data["writing"] == True:
        data["current_item"] = message.text
        write_file(message.chat.id,data)
        with open(VAHTA_DATES_IMG, 'rb') as photo:
            await bot.send_photo(message.chat.id, photo, caption=VAHTA_DATES_TEXT, reply_markup=gen_admin_vahta_day_markup())


async def sched():
    chat_ids = os.listdir("jsons")
    for id in chat_ids:
        id = id.replace(".json", "")
        data = read_file(id)
        for item in data.keys():
            text = ""
            if "date" in f"{data[item]}":
                for every_vahta in data[item]:
                    date = every_vahta['date']
                    today = datetime.today()
                    if str((today + timedelta(1)).date()) == date:
                        vahters_text = ""
                        for vahter in every_vahta['vahter']:
                            vahters_text += f"{vahter}, "
                        vahta_text = (f"{vahters_text} у вас завтра вахта: {every_vahta['item']}\n"
                                      f"Дата: {every_vahta['date']}\n"
                                      f"Время: {every_vahta['time']}\n")
                        with open(VAHTA_DATES_IMG, 'rb') as photo:
                            await bot.send_photo(id, photo, caption=vahta_text)



async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(sched, 'cron', hour=19, minute=3)
    scheduler.start()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.create_task(bot.polling(none_stop=True, interval=0))
    loop.run_forever()
