import vk_api, vk
from vk_api.utils import get_random_id
import datetime, random, json
import json
import requests
import sqlite3

vk_session = vk_api.VkApi(token='b7ace591af1d009bed07258f5bb30f3455b18b3ffce10fdf21ae0fd9a9f80aedd636e5e84ea997ed6701c')
random.seed()
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

longpoll = VkBotLongPoll(vk_session, 203814419)
vk = vk_session.get_api()


def saymessage(message, chatid):
    vk.messages.send(
        key='265b9078df036d8b0bc08fa119f73547cb9e6fd9',
        server='https://lp.vk.com/wh203658568',
        ts='1',
        random_id=get_random_id(),
        message=message,
        chat_id=chatid
    )


def answer_message(chat_id, id_message, peer_id, text):
    query_json = json.dumps({"peer_id": peer_id, "conversation_message_ids": [id_message], "is_reply": True})
    vk_session.method('messages.send', {
        'chat_id': chat_id,
        'forward': [query_json],
        'message': text,
        'random_id': get_random_id()})


def DateToday(date):
    if date == 1:
        return 'Понедельник'
    elif date == 2:
        return 'Вторник'
    elif date == 3:
        return 'Среда'
    elif date == 4:
        return 'Четверг'
    elif date == 5:
        return 'Пятница'
    elif date == 6:
        return 'Суббота'
    elif date == 7:
        return 'Воскресенье'


def GetTimetable(group):
    url = 'https://rasp.omgtu.ru'
    # получаем json со всеми группами с такими или близкими названиями (ИВТ-201 и ЗИВТ-201)
    response = requests.get(f"{url}/api/search?term={group}&type=group")
    gettedjson = json.loads(response.text)

    print(gettedjson)
    # отсортировываем json чтобы получить id нужной группе, указанной в переменной group
    for label in gettedjson:
        if label['label'] == group:
            print(label['id'])
            gettedid = str(label['id'])

    # получаем даты начала и конца недели
    todaydate = datetime.datetime.today().isoweekday()
    startdate = datetime.datetime.today() - datetime.timedelta(todaydate - 1)
    finishdate = datetime.datetime.today() + datetime.timedelta(7 - todaydate)
    print(startdate.strftime('%Y.%m.%d'))
    print(finishdate.strftime('%Y.%m.%d'))

    # получаем json с расписанием группы
    response = requests.get(
        f"{url}/api/schedule/group/{gettedid}?"
        f"start={startdate.strftime('%Y.%m.%d')}&finish={finishdate.strftime('%Y.%m.%d')}&lng=1")
    print(response.json())

    gettedjson = json.loads(response.text)
    return gettedjson


def CreateTable(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS groups(
        studgroup TEXT,
    	auditorium TEXT,
    	beginLesson TEXT,
    	date TEXT,
    	dayOfWeekString TEXT,
    	discipline TEXT,
    	endLesson TEXT,
    	kindOfWork TEXT,
    	lecturer TEXT,
    	lecturerOid TEXT,
    	stream TEXT,
    	subGroup TEXT);""")
    conn.commit()


if __name__ == '__main__':
    conn = sqlite3.connect('timetables.db')
    cur = conn.cursor()
    group = 'ИВТ-201'

    gettedjson = GetTimetable(group)

for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        if 'ТТ расписание' in str(event):
            if event.from_chat:
                today = datetime.datetime.today().strftime('%Y.%m.%d')
                cur.execute(f"SELECT * FROM groups WHERE studgroup = '{group}' AND date = '{today}';")
                all_results = cur.fetcshall()

                message = f"{DateToday(datetime.datetime.now().isoweekday())}\n"
                for result in all_results:
                    if (result[1] == 'В.А.33') or (result[1] == 'В.А.36'):  # result[1] = аудитория
                        cur.execute(f"SELECT * FROM teachers WHERE lecturerOid = '{result[9]}';")
                        url = cur.fetchone()
                        urltext = f"\n{url[1]}"
                    else:
                        url = ['', '']
                        urltext = ''

                    # result[5] = пара; result[8] = препод; result[1] = аудитория; result[2] = начало пары;
                    # result[6] = конец пары; result[11] = подгруппа
                    if result[11] is None:
                        message = message + f"{result[5]} ({result[8]}) в {result[1]} с {result[2]} по {result[6]}{urltext}\n"
                    else:
                        message = message + f"{result[5]} ({result[8]}) в {result[1]} с {result[2]} по {result[6]} у {result[11]}{urltext}\n"

                vk.messages.send(
                    key='4b413a03341032f343f6875f9a4e12e06a8d4a44',
                    server='https://lp.vk.com/wh203814419',
                    ts='4',
                    random_id=get_random_id(),
                    message=message,
                    chat_id=event.chat_id
                )
                print(message)
