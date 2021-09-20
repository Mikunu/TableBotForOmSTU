import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
import json
import random
import requests
import datetime
import sqlite3
import threading
import time
import schedule
import sys

def send_Message(message, chatid):
    vk.messages.send(
        key='265b9078df036d8b0bc08fa119f73547cb9e6fd9',
        server='https://lp.vk.com/wh203658568',
        ts='1',
        random_id=get_random_id(),
        message=message,
        chat_id=chatid
    )


def dateToday(date):
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


def GetTimetable(group, selectedDay):
    url = 'https://rasp.omgtu.ru'
    # получаем json со всеми группами с такими или близкими названиями (ИВТ-201 и ЗИВТ-201)
    response = requests.get(f"{url}/api/search?term={group}&type=group")
    gettedjson = json.loads(response.text)

    # отсортировываем json чтобы получить id нужной группе, указанной в переменной group
    for label in gettedjson:
        if label['label'] == group:
            gettedid = str(label['id'])

    # получаем даты начала и конца недели
    dayOfWeek = selectedDay.isoweekday()
    startdate = selectedDay - datetime.timedelta(dayOfWeek - 1)
    finishdate = selectedDay + datetime.timedelta(7 - dayOfWeek)


    # получаем json с расписанием группы
    response = requests.get(
        f"{url}/api/schedule/group/{gettedid}?"
        f"start={startdate.strftime('%Y.%m.%d')}&finish={finishdate.strftime('%Y.%m.%d')}&lng=1")
    # print(response.json())

    gettedjson = json.loads(response.text)
    return gettedjson


def getSingleLesson(time, selectedDay, gotJson, chatid):
    entrymessage = f"Следующая пара скоро начнётся!\n---------------------------\n"
    message = ''
    urltext = ''
    for result in gotJson:
        if result["date"] == selectedDay.strftime('%Y.%m.%d'):
            if result['beginLesson'] == time:
                dbResult = cur.execute(f"SELECT * FROM disciplinelinks WHERE chatid={chatid}").fetchall()
                if result['auditorium'].find('В.А') != -1:
                    for elem in dbResult:
                        if result['discipline'].find(elem[2]) != -1:
                            urltext = elem[3]
                if result['subGroup'] is None:
                    message += f"{result['discipline']}\n{result['lecturer']}\n" \
                               f"В {result['auditorium']} с {result['beginLesson']} по {result['endLesson']}\n{urltext}\n\n"
                else:
                    message += f"{result['discipline']}\n{result['lecturer']}\n" \
                               f"В {result['auditorium']} с {result['beginLesson']} по {result['endLesson']} " \
                               f"у {result['subGroup']}\n{urltext}\n\n"
    entrymessage += message
    return entrymessage

def makeTable(selectedDay, gotJson, chatid):
    entrymessage = f"{dateToday(selectedDay.isoweekday())}, {selectedDay.strftime('%d.%m')}\n---------------------------\n"
    message = ''
    for result in gotJson:
        if result["date"] == selectedDay.strftime('%Y.%m.%d'):
            urltext = ''
            dbResult = cur.execute(f"SELECT * FROM disciplinelinks WHERE chatid={chatid}").fetchall()
            if result['auditorium'].find('В.А') != -1:
                for elem in dbResult:
                    if result['discipline'].find(elem[2]) != -1:
                        urltext = elem[3]

            if result['subGroup'] is None:
                message += f"{result['discipline']}\n{result['lecturer']}\n" \
                           f"В {result['auditorium']} с {result['beginLesson']} по {result['endLesson']}\n{urltext}\n\n"
            else:
                message += f"{result['discipline']}\n{result['lecturer']}\n" \
                           f"В {result['auditorium']} с {result['beginLesson']} по {result['endLesson']} " \
                           f"у {result['subGroup']}\n{urltext}\n\n"

    if len(message) == 0:
        message = 'Сегодня пар нет, отдыхайте'

    entrymessage += message
    return entrymessage


def notifier(cur):
    time = datetime.datetime.now() + datetime.timedelta(minutes=10)
    time = time.strftime('%H:%M')
    if time == '7:30':
        result = cur.execute(f"SELECT * FROM chats").fetchall()
        selectedDay = datetime.datetime.today()
        for elem in result:
            message = makeTable(selectedDay, GetTimetable(elem[1], selectedDay), elem[0])
            send_Message(message, int(elem[0]))

    times = ['08:00', '09:40', '11:20', '14:00', '15:40', '17:20', '19:00']
    for timeElem in times:
        if timeElem == time:
            result = cur.execute(f"SELECT * FROM chats").fetchall()
            selectedDay = datetime.datetime.today()
            for elem in result:
                message = getSingleLesson(time, selectedDay, GetTimetable(elem[1], selectedDay), elem[0])
                if len(message) > 65:
                    send_Message(message, int(elem[0]))

def run_continuously(interval=1):
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return cease_continuous_run


if __name__ == '__main__':
    with open(r"C:\Users\rusla\PycharmProjects\TatarTechBot2.0\loginstuff.json", "r") as read_file:
        data = json.load(read_file)
        vk_session = vk_api.VkApi(token=data[0]['token'])
        random.seed()

        longpoll = VkBotLongPoll(vk_session, data[0]['group_id'])
        vk = vk_session.get_api()

    conn = sqlite3.connect(r'C:\Users\rusla\PycharmProjects\TatarTechBot2.0\timetables.db', check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS chats(
        chatid text,
        groupname text
        );""")

    cur.execute("""CREATE TABLE IF NOT EXISTS disciplinelinks(
        lineid int,
        chatid text,
        discipline text,
        link text
        );""")
    conn.commit()

    schedule.every(1).minutes.do(notifier, cur)
    stop_run_continuously = run_continuously()

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            if 'ТТ, расписание' in str(event):
                if event.from_chat:
                    selectedDay = datetime.datetime.today()
                    if event.message.text[14:].find('завтра') != -1:
                        selectedDay += datetime.timedelta(days=1)
                        if event.message.text[14:].find('после') != -1:
                            selectedDay += datetime.timedelta(days=1)

                    message = makeTable(selectedDay, GetTimetable('ИВТ-201', selectedDay), str(event.chat_id))
                    send_Message(message, event.chat_id)

            elif 'TT, init' in str(event):
                if event.from_chat:
                    # TT init ИВТ-202
                    group = event.message.text[8:]
                    chat = [str(event.chat_id), group]
                    cur.execute(f"SELECT COUNT ({event.chat_id}) from chats WHERE chatid = {event.chat_id}")
                    if cur.fetchall() == 0:
                        cur.execute("INSERT INTO chats VALUES(?, ?);", chat)
                        send_Message(f'Беседа успешно инициализирована, ваша группа {group}', event.chat_id)
                        conn.commit()
                    else:
                        cur.execute(f"SELECT * from chats WHERE chatid = {event.chat_id}")
                        group = cur.fetchall()
                        send_Message(f'Группа {group[0][1]} уже инициализирована!', event.chat_id)

            elif 'TT, uninit' in str(event):
                if event.from_chat:
                    cur.execute(f"SELECT COUNT ({event.chat_id}) from chats WHERE chatid = {event.chat_id}")
                    if cur.fetchall() == 0:
                        send_Message(f'Беседа не инициализирована')
                    else:
                        cur.execute(f"DELETE FROM chats WHERE chatid = {event.chat_id}")
                        conn.commit()
                        send_Message(f'Связь беседы и группы разорвана')

            elif 'TT, добавить ссылку' in str(event):
                if event.from_chat:
                    '''
                    Математика
                    http://b21523.vr.mirapolis.ru/mira/miravr/7544736809
                    При входе в систему необходимо указать свою фамилию и номер группы.

                    Дизайн интерфейса информационных систем
                    http://b21523.vr.mirapolis.ru/mira/miravr/6456350497
                    '''
                    message = event.message.text[20:]
                    if message.find('"') == -1:
                        send_Message('Ошибка в вводе команды, отсутствуют кавычки,', event.chat_id)
                    result = int(cur.execute(f"SELECT count(*) FROM disciplinelinks").fetchone()[0])
                    print(result)
                    if result == 0:
                        linkid = 0
                    else:
                        linkid = result + 1

                    disciplinename = message[message.find('"') + 1:message.rfind('"')]
                    print(disciplinename)
                    '''
                    cur.execute(f"SELECT * FROM disciplinelinks WHERE discipline={disciplinename}")
                    result = cur.fetchone()[0][0]
                    print(result)
                    if result is not None:
                        send_Message('Данный предмет уже добавлен')
                        '''
                    link = message[message.rfind('"') + 2:]
                    linkinfo = [linkid, event.chat_id, disciplinename, link]
                    cur.execute("INSERT INTO disciplinelinks VALUES (?, ?, ?, ?);", linkinfo)
                    conn.commit()
                    send_Message(f'Ссылка {link} связана с {disciplinename}', event.chat_id)

            elif 'ТТ,' in str(event):
                if event.from_chat:
                    send_Message('Такой команды нет', event.chat_id)