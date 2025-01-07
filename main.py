from requests import get as httpget
from random import randint
import team
import json
import configparser
import vk

configfile = 'prisma.ini'
config = configparser.ConfigParser()
config.read(configfile)

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
    global ts

    print('[SYSTEM] Getting new Long Poll server...')
    new_lp = vk.groups.getLongPollServer(group_id=group_id)

    if not 'longpoll' in config:
        config.add_section('longpoll')
    config['longpoll']['server'] = new_lp['server']
    config['longpoll']['key'] = new_lp['key']
    ts = new_lp['ts']
    saveConfig()

# отправка сообщения
def sendMessage(peer_id: int, text: str, keyboard: str = ""):
    try:
        vk.messages.send(peer_id=peer_id,
                        message=text,
                        random_id=randint(0, 4294967296),
                        keyboard=keyboard)
    except Exception as e:
        print("[ERROR] Failed to send message to", peer_id, "!", e)
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

        command = payload.get('command', "")
        data = int(payload.get('data', 0))

        # команда "начать" или соответствующая кнопка (приветственное сообщение)
        if command == "start" or text.lower() == "начать":
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
        # нажатие кнопки "хочу сюда"
        elif command == "reg":
            user = vk.users.get(user_ids=from_id,fields='is_verified',lang=0)
            username = "{0} {1}".format(user[0]['last_name'], user[0]['first_name'])
            print("[DATA] VK username:", from_id, ", is_verified:", user[0]['is_verified'])
            # удобства с ВКшным payload на этом закончились, теперь надо кэшировать всё ручками
            usercache.update({from_id: [username, 1, data]})

            # кнопки "У меня нет отчества" и "Начать заново"
            keyboard = json.dumps({
                "inline": True,
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
                sendMessage(team.get_director(direction_sel)[0], msg)
                # т.к. это последняя стадия регистрации, отправляем сообщение "Спасибо" и удаляем юзера из кэша
                sendMessage(from_id, team.thanks)
                del usercache[from_id]
        
# главный цЫкл бота
try:
    if not 'longpoll' in config:
        print('[SYSTEM] No Long Poll server config are found!')
        updateLongPoll()

    ts = config.getint('longpoll', 'ts')
    print('[SYSTEM] Bot is started.')
    while True:
        events = httpget(config['longpoll']['server'], params={'act': 'a_check',
                                                               'key': config['longpoll']['key'],
                                                               'ts': ts, 'wait': 25})
        error = events.json().get('failed')
        if error in (2, 3):
            updateLongPoll()
        else:
            ts = events.json()['ts']
            #print(events.json())
            takeMessage(events.json())
        
except KeyboardInterrupt:
    saveConfig()
    print('Exiting.')
    exit(0)
