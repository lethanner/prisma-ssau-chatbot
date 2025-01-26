# я плохо пишу на python, простите

from requests import get as httpget
import team
import logging
import json
import configparser
import vk
from time import sleep

configfile = 'prisma.ini'
config = configparser.ConfigParser()
config.read(configfile)

# логирование оставляю для отлова ошибок в случае их возникновения
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
loghandler = logging.FileHandler('prismabot.log', 'a', 'utf-8')
loghandler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(loghandler)

vk = vk.API(access_token=config['auth']['group'],v=5.199)
group_id = config.getint('misc','group_id')

dirs_keyboard = json.dumps(team.generate_keyboard())
usercache = {}

# конфиг и long polling
ts = 0
def saveConfig():
    print('[SYSTEM] Saving', configfile, '... ', end='')
    config['longpoll']['ts'] = str(ts)
    with open(configfile, 'w') as file:
        config.write(file)
    print('done.')

def updateLongPoll():
    try:
        global ts

        print('[SYSTEM] Getting new Long Poll server...')
        new_lp = vk.groups.getLongPollServer(group_id=group_id)

        if not 'longpoll' in config:
            config.add_section('longpoll')
        config['longpoll']['server'] = new_lp['server']
        config['longpoll']['key'] = new_lp['key']
        ts = new_lp['ts']

        logger.debug("Got new Long Poll server config")
        logger.debug(new_lp)
        saveConfig()
    except Exception as e:
        logger.error(e, exc_info=1)
        print("[ERROR] Failed to get Long Poll server config!", e)

# отправка сообщения
def sendMessage(peer_id: int, text: str, keyboard: str = '{"buttons": []}'):
    try:
        vk.messages.send(peer_id=peer_id,message=text,random_id=0,
                         keyboard=keyboard)
        print("[BOT] to id{0}: {1}".format(peer_id, text))
        logger.info("To id%i: %s, keyboard: %s", peer_id, text, keyboard)
    except Exception as e:
        print("[ERROR] Failed to send message to", peer_id, "!", e)
        logger.error("Can't send message to %i", peer_id)
        pass

def takeMessage(events):
    # обработка всех событий по очереди
    for event in events['updates']:
        obj = {}
        payload = {}
        if event['type'] == 'message_new': # если новое сообщение
            obj = event['object']['message']
            payload = json.loads(obj.get('payload', '{"command": "none"}'))
        elif event['type'] == 'message_event': # если событие нажатия callback-кнопки
            obj = event['object']
            payload = obj['payload']
        else: # остальное пропускаем
            continue

        text = obj.get('text', "")
        from_id = obj['peer_id']
        print("[MESSAGE] id{0}: {1}; payload: {2}".format(from_id, text, payload))
        logger.info("From id%i: %s, payload: %s", from_id, text, payload)

        command = payload.get('command', "")
        data = int(payload.get('data', 0))

        # команда "начать" или соответствующая кнопка (приветственное сообщение)
        if command == "start" or text.lower() == "начать":
            director = next(((key, value) for key, value in team.directorate.items() if value[0] == from_id), None)
            # если кнопку нажал замыка, то ему просто вываливается инфа о нём
            if (director):
                sendMessage(from_id, "{0} - {1}".format(director[1][1], director[0]))
            else: # остальные получат предложение начать выбирать направление
                sendMessage(from_id, team.greeting, dirs_keyboard)
                usercache.pop(from_id, None) # удалить юзера из кэша (на случай, если он начнёт заново)
        # нажатие кнопки с названием направления (выброс описания с кнопкой "хочу сюда")
        elif command == "descr" and 0 <= data < team.dir_count:
            keyboard = json.dumps({
                "inline": True,
                "buttons": [[{
                    "action": {
                        "type": "callback",
                        "payload": '{"command": "reg", "data": ' + str(data) + '}',
                        "label": "Хочу сюда!"
                    },
                    "color": "positive"
                }]]})
            sendMessage(from_id, team.dir_description(data), keyboard)
        elif text == "/lol" and from_id == config.getint('auth','bot_admin'):
            a = 1/0
        # нажатие кнопки "хочу сюда"
        elif command == "reg":
            user = vk.users.get(user_ids=from_id,fields='is_verified',lang=0)
            username = "{0} {1}".format(user[0]['last_name'], user[0]['first_name'])
            print("[DATA] VK username:", from_id, ", is_verified:", user[0]['is_verified'])
            # удобства с ВКшным payload на этом закончились, теперь надо кэшировать всё ручками
            usercache.update({from_id: [username, 1, data]})

            # кнопки "У меня нет отчества" и "Начать заново"
            keyboard = json.dumps({
                "one_time": True,
                "buttons": [[{
                    "action": {
                        "type": "text",
                        "payload": '{"command": "no_surname"}',
                        "label": "У меня нет отчества"
                    },
                    "color": "secondary"
                }],[{
                    "action": {
                        "type": "text",
                        "payload": '{"command": "start"}',
                        "label": "Отменить выбор"
                    },
                    "color": "negative"
                }]]})
            sendMessage(from_id, team.choose_msg(data, username), keyboard)
        # если юзер уже в кэше, то работаем с ним вот так
        elif from_id in usercache:
            # если была кнопка "нет отчества", перескакиваем сразу на stage 2
            if command == "no_surname":
                usercache[from_id][1] = 2
                # сразу просим номер группы
                sendMessage(from_id, team.group_request)
                continue

            stage = usercache[from_id][1]
            direction_sel = usercache[from_id][2]
            if stage == 1: # стадия ввода О/ФИО
                # если в введённом тексте есть пробелы, считаем, что ввели больше, чем отчество
                # и в таком случае заменяем вообще всё изначальное ФИ на введённый текст
                if text.count(' ') > 0:
                    usercache[from_id][0] = text
                # если пробелов нет, значит, вероятно, ввели одно только отчество
                # поэтому просто дополняем ВКшное ФИ введённым текстом
                else:
                    usercache[from_id][0] += ' ' + text
                # и потом просим у клиента номер группы
                sendMessage(from_id, team.group_request)
                usercache[from_id][1] = 2
            elif stage == 2:
                # уведомляем о регистрации замыкающего направления, худрука и администратора
                msg = "[id{0}|{1}] подал(а) заявку на участие в: {2}.\r\nНомер группы: {3}".format(
                    from_id, usercache[from_id][0],
                    team.directions[direction_sel]['name'],
                    text)
                dir_director = team.get_director(direction_sel)[0]
                if dir_director != 0 and dir_director != team.directorate['owner'][0]:
                    sendMessage(dir_director, msg)
                sendMessage(team.directorate['owner'][0], msg)
                sendMessage(team.directorate['admin'][0], msg)
                # т.к. это последняя стадия регистрации, отправляем сообщение "Спасибо" и удаляем юзера из кэша
                # дополнительно сохраняем инфу в файл, на случай если замыки случайно удалят сообщения
                sendMessage(from_id, team.thanks.format(config['misc']['chat_url']))
                with open("database/{0}.txt".format(team.directions[direction_sel]['codename']), 'a+', encoding='utf-8') as file:
                    file.write("{0}\r\nhttps://vk.com/id{1}\r\n\r\n".format(usercache[from_id][0], from_id))
                del usercache[from_id]
        
# главный цЫкл бота
try:
    if not 'longpoll' in config:
        print('[SYSTEM] No Long Poll server config are found!')
        updateLongPoll()

    ts = config.getint('longpoll', 'ts')
    print('[SYSTEM] Bot is started.')
    logger.info("Bot is started.")
    while True:
        # блок получения сообщений через longpoll
        try:
            events = httpget(config['longpoll']['server'], params={'act': 'a_check',
                                                                'key': config['longpoll']['key'],
                                                                'ts': ts, 'wait': 25},
                                                                timeout=30)
            logger.debug(events.json())
            error = events.json().get('failed')
            if error in (2, 3):
                updateLongPoll()
                continue

        except Exception as e:
            print("[ERROR] Long Poll error!!!!!")
            logger.error("Fatal LongPoll error!")
            logger.error(e, exc_info=1)
            print("[SYSTEM] Waiting 30 seconds")
            sleep(30)
            updateLongPoll()
            pass

        # блок обработки сообщений (и ошибок, с ними связанных)
        try:
            ts = events.json()['ts']
            #print(events.json())
            takeMessage(events.json())

        except Exception as e:
            print("[ERROR] Something went wrong!!!", e)
            sendMessage(config.getint('auth','bot_admin'), "боту плохо, посмотри логи... " + str(e))
            logger.error(e, exc_info=1)
            pass
        
except KeyboardInterrupt:
    saveConfig()
    print('Exiting.')
    logger.info("Stopping.")
    exit(0)