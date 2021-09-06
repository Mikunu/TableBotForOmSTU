import vk_api, vk
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
import datetime, random, json
import json
import requests
import sqlite3
import re

def send_Message(message, chatid):
    vk.messages.send(
        key='265b9078df036d8b0bc08fa119f73547cb9e6fd9',
        server='https://lp.vk.com/wh203658568',
        ts='1',
        random_id=get_random_id(),
        message=message,
        chat_id=chatid
    )


def addlessons(gettedjson, cur, conn):
    for timetable in gettedjson:
        lesson = [
            group,
            timetable['auditorium'],
            timetable['beginLesson'],
            timetable['date'],
            timetable['dayOfWeekString'],
            timetable['discipline'],
            timetable['endLesson'],
            timetable['kindOfWork'],
            timetable['lecturer'],
            timetable['lecturerOid'],
            timetable['stream'],
            timetable['subGroup']]
        cur.execute("INSERT INTO groups VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", lesson)
        conn.commit()


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

    # print(gettedjson)
    # отсортировываем json чтобы получить id нужной группе, указанной в переменной group
    for label in gettedjson:
        if label['label'] == group:
            print(label['id'])
            gettedid = str(label['id'])

    # получаем даты начала и конца недели
    todaydate = datetime.datetime.today().isoweekday()
    startdate = datetime.datetime.today() - datetime.timedelta(todaydate - 1)
    finishdate = datetime.datetime.today() + datetime.timedelta(7 - todaydate)
    # print(startdate.strftime('%Y.%m.%d'))
    # print(finishdate.strftime('%Y.%m.%d'))

    # получаем json с расписанием группы
    response = requests.get(
        f"{url}/api/schedule/group/{gettedid}?"
        f"start={startdate.strftime('%Y.%m.%d')}&finish={finishdate.strftime('%Y.%m.%d')}&lng=1")
    # print(response.json())

    gettedjson = json.loads(response.text)
    return gettedjson


def CreateTable(cur, conn):
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


def makeTable(cur, event, selectedDay):
    cur.execute(f"SELECT groupname FROM chats WHERE chatid ='{str(event.chat_id)}';")
    group = cur.fetchall()[0][0]

    message = f"{DateToday(selectedDay.isoweekday())}\n---------------------------\n"
    cur.execute(f"SELECT * FROM groups WHERE studgroup = '{group}' AND date = '{selectedDay.strftime('%Y.%m.%d')}';")
    all_results = cur.fetchall()
    if len(all_results) == 0:
        if selectedDay is not None:
            message = message + 'В этот день пар нет, отдыхайте'
        else:
            message = message + 'Сегодня пар нет, отдыхайте'
    else:
        for result in all_results:
            '''
            if (result[1] == 'В.А.33') or (result[1] == 'В.А.36'):  # result[1] = аудитория
                cur.execute(f"SELECT * FROM teachers WHERE lecturerOid = '{result[9]}';")
                url = cur.fetchone()
                urltext = f"\n{url[1]}"
            else:
                url = ['', '']
                urltext = ''
            '''
            urltext = ''
            # print(message)
            # print(result)
            # result[5] = пара; result[8] = препод; result[1] = аудитория; result[2] = начало пары;
            # result[6] = конец пары; result[11] = подгруппа
            if result[11] is None:
                message = message + f"{result[5]} ({result[8]}) в {result[1]} с {result[2]} по {result[6]}{urltext}\n\n"
            else:
                message = message + f"{result[5]} ({result[8]}) в {result[1]} с {result[2]} по {result[6]} у {result[11]}{urltext}\n\n"

    return message

def check_Date_Format(date):
    for symbol in date:
        if symbol.isdigit() or symbol == '.':
            return True
    return False


if __name__ == '__main__':

    with open("loginstuff.json", "r") as read_file:
        data = json.load(read_file)
        print(data[0]['token'])
        vk_session = vk_api.VkApi(token=data[0]['token'])
        random.seed()

        longpoll = VkBotLongPoll(vk_session, data[0]['group_id'])
        vk = vk_session.get_api()

    conn = sqlite3.connect('timetables.db')
    cur = conn.cursor()
    CreateTable(cur, conn)
    cur.execute("""CREATE TABLE IF NOT EXISTS chats(
    chatid text,
    groupname text
    );""")

    cur.execute("""CREATE TABLE IF NOT EXISTS disciplines(
    chatid text,
    disciplineOid text,
    discipline text,
    link text
    );""")
    conn.commit()

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            if 'ТТ, расписание' in str(event):
                if event.from_chat:
                    day = None
                    month = None
                    year = None
                    if len(event.message.text) >= 15:
                        try:
                            date = event.message.text[15:]
                            if check_Date_Format(date):
                                # 04.09.2021
                                # 4
                                print(date)
                                today = datetime.datetime.today()
                                if len(date) > 2 and date.find('.') != -1:
                                    day = date[:date.find('.')]
                                    date = date[date.find('.') + 1:]
                                    if date.find('.') != -1:
                                        day = date[:date.find('.')]
                                        date = date[date.find('.') + 1:]
                                        if date.find('.') != -1:
                                            month = date[:date.find('.')]

                                    else:
                                        if int(day) < today.day:
                                            month = today.month + 1
                                            if month == 13:
                                                month = 1
                                                year = today.year + 1
                                            else:
                                                year = today.year
                                        else:
                                            month = today.month
                                            year = today.year

                                else:
                                    day = date
                                    if int(day) < today.day:
                                        month = today.month + 1
                                        if month == 13:
                                            month = 1
                                            year = today.year + 1
                                        else:
                                            year = today.year
                                    else:
                                        month = today.month
                                        year = today.year

                                date = f'{year}.{month}.{day}'
                                selectedDay = datetime.datetime.strptime(date, '%Y.%m.%d')
                            else:
                                send_Message('Неверный формат команды, выводится расписание на сегодня')
                            '''
                            

                            print(f'Day: {day}\nMonth: {month}\nYear: {year}')
                            
                            if date.find('.') != -1:
                                day = date[:date.find('.')]
                                date = date[date.find('.') + 1:]
                                print(date)
                                print(f'Day: {day}')
                                if date.find('.') != -1:
                                    month = date[:date.find('.')]
                                    message_Text = date[date.find('.'):]
                                    print(date)
                                    print(f'Month: {month}')
                                    if date.find('.') != -1:
                                        year = date[:date.find('.')]
                                        date = date[date.find('.'):]
                                        print(date)
                                        print(f'Year: {year}')
                                        '''
                        except:
                            pass
                    else:
                        selectedDay = datetime.datetime.today()
                    message = makeTable(cur, event, selectedDay)
                    message = f'Day: {day}\nMonth: {month}\nYear: {year}'
                    send_Message(message, event.chat_id)

            elif 'ТТ, test' in str(event):
                if event.from_chat:
                    regex = re.compile('TT, test ([\s\S]+\-\d+)')
                    message = regex.match(event.message.text, event.chat_id)
                    print(message)

            elif 'ТТ, завтра' in str(event):
                if event.from_chat:
                    selectedDay = datetime.datetime.today() + datetime.timedelta(days=1)
                    message = makeTable(cur, event, selectedDay)

                    send_Message(message, event.chat_id)

            elif 'ТТ, послезавтра' in str(event):
                if event.from_chat:
                    selectedDay = datetime.datetime.today() + datetime.timedelta(days=2)
                    message = makeTable(cur, event, selectedDay)

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
                        addlessons(GetTimetable(group), cur, conn)
                    else:
                        cur.execute(f"SELECT * from chats WHERE chatid = {event.chat_id}")
                        group = cur.fetchall()
                        send_Message(f'Группа {group[0][1]} уже инициализирована!', event.chat_id)

            elif 'TT, uninit' in str(event):
                if event.from_chat:
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
                    linkinfo = [event.chat_id]
                    cur.execute("INSERT INTO lecturers VALUES (?, ?, ?);", )

            elif 'ТТ,' in str(event):
                if event.from_chat:
                    send_Message('Такой команды нет', event.chat_id)
