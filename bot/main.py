# модули Python
from dataclasses import dataclass, field
from os.path import exists
from time import time
import logging
import json

# библиотеки
import vk

# модули бота
import longpoll
import keyboards

# логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
loghandler = logging.FileHandler('prismabot.log', 'a', 'utf-8')
loghandler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(loghandler)

def loadConfiguration():
    conf = {}
    try:
        with open('userdata/config.json', 'r', encoding='utf-8') as f:
            print("[SYSTEM] Loading config.json")
            conf = json.load(f)
    except FileNotFoundError:
        print('[ERROR] config.json not found')
        logger.error('config.json not found')
    except json.JSONDecodeError:
        print('[ERROR] config.json parsing failed')
        logger.error('Failed to parse config.json')
    
    return conf
        
# загрузить конфигурацию из файла
config = loadConfiguration()
if not config: exit(0)
dir_count = len(config['directions'])
# pyright: reportPossiblyUnboundVariable=none

vk = vk.API(access_token=config['auth_token'],v=5.199)
receiver = longpoll.LongPoll(config['group_id'], vk, logger)
# pyright: reportAttributeAccessIssue=none

# создать файл registered.json при отсутствии
if not exists('userdata/registered.json'):
    with open('userdata/registered.json', 'w+', encoding='utf-8') as f:
        print('[INFO] Creating empty registered.json')
        f.write('{"newbies": [], "manual": []}')

@dataclass
class UserData:
    vkname: str = ""
    name: str = ""
    stage: int = 0
    group_no: str = '-'
    birthday: str = '-'
    selection: set[int] = field(default_factory=set)
    old_warning: bool = False

usercache = dict()

director_id = lambda dir: config['directorate'][dir]['id']
director_name = lambda dir: config['directorate'][dir]['name']
def getDirector(id: int) -> tuple:
    for dir in config['directions']:
        if id == director_id(dir['codename']):
            return (director_name(dir['codename']),dir['name'])
    return ()

# отправка сообщений
def sendMessage(peer_id: int, text: str, keyboard: str = ''):
    try:
        vk.messages.send(peer_id=peer_id,message=text,random_id=0, 
                         keyboard=keyboard)
        print(f"[BOT] to id{peer_id}: {text}")
        logger.info("To id%i: %s, keyboard: %s", peer_id, text, keyboard)
    except Exception as e:
        print("[ERROR] Failed to send message to", peer_id, "!", e)
        logger.error("Can't send message to %i", peer_id, exc_info=True)

# обработка входящих сообщений (и событий)
def processMessage(events):
    global config
    for event in events['updates']:
        if event['type'] == 'message_new': # текстовое
            obj = event['object']['message']
            payload = json.loads(obj.get('payload', '{"command": "none"}'))
        elif event['type'] == 'message_event': # нажатие callback-кнопки
            obj = event['object']
            payload = obj['payload']
        else: # остальное пропускаем
            continue
    
        text = obj.get('text', '')
        from_id = obj['peer_id']
        command = payload.get('command', "")
        client = event['object'].get('client_info', ())
        data = int(payload.get('data', 0))
        sel_force_render = False

        # пропуск сообщений из бесед (если бот был в них добавлен)
        if from_id > 2000000000:
            continue

        print(f"[MESSAGE] id{from_id}: {text}; payload: {payload}")
        logger.info("From id%i: %s, payload: %s", from_id, text, payload)

        if command not in ('none', 'start') and not usercache.get(from_id):
            sendMessage(from_id, '⚠️ По техническим причинам сессия была сброшена.\n\nПожалуйста, напиши "Начать" и подай заявку заново.')
            continue

        # === команда "заново" (с сохранением выбора направлений) ===
        if command == 'again':
            usercache[from_id].stage = 0
            usercache[from_id].name = usercache[from_id].vkname
            sel_force_render = True
            command = 'none'

        # === команда отмены выбора направления ===
        elif command == 'deselect':
            usercache[from_id].selection.discard(data)
            # если после снятия выбора ничего не осталось, возвращаем
            # в самое начало, имитируя повторное нажатие кнопки "начать"
            if len(usercache[from_id].selection) == 0: command = 'start'
            # иначе триггеруем отображение списка
            else: sel_force_render = True

        # === "начать" ===
        if command == 'start' or text.lower() == 'начать':
            director = getDirector(from_id)
            # замыкающему приходит только инфа о нём
            if director:
                sendMessage(from_id, "{0}, ты замыкаешь направление: {1}.".format(*director))
            else: 
                usercache.pop(from_id, None)
                usercache[from_id] = UserData()
                # достать ФИ юзера с его страницы ВК
                user = vk.users.get(user_ids=from_id,fields='is_verified',lang=0)[0]
                usercache[from_id].vkname = usercache[from_id].name = f"{user['last_name']} {user['first_name']}"
                sendMessage(from_id, "Выбери направление в списке, чтобы узнать о нём больше!\nНе забывай, что список прокручивается.",
                            keyboards.generate_dirs_keyboard(config['directions']))
                
                if client and (not client['keyboard'] or not client['inline_keyboard'] or 'callback' not in client['button_actions']):
                    sendMessage(from_id, '⚠️ Внимание! Похоже, у тебя старая версия ВКонтакте.\n\n'
                                'Если ты не видишь кнопок или они не работают, напиши "Олд", чтобы подать заявку вручную.')

        # === нажатие на направление (выброс описания с кнопкой "хочу сюда!") ===
        elif command == 'descr' and 0 <= data <= dir_count:
            director = config['directorate'][config['directions'][data]['codename']] 
            descr = '{0}\n\n{1}амыкающий направления - @id{2} ({3}).'.format(config['directions'][data]['description'], 
                                                                                 *('З', director['id'], director['name']) if director['id']
                                                                                 else ('Временный з',   director_id('owner'), director_name('owner'))) 
            sendMessage(from_id, descr, keyboards.get_sel_button(data))

        # === завершение регистрации ===
        elif (command == 'submit' or text.lower() == 'подтвердить') and usercache[from_id].stage == 4:
            with open('userdata/registered.json', 'r+', encoding='utf-8') as f:
                usr = usercache[from_id]
                database = json.load(f)
                database['newbies'].append({"name": usr.name,
                                            "birthday": usr.birthday,
                                            "group": usr.group_no,
                                            "vk": 'https://vk.com/id' + str(from_id),
                                            "roles": ', '.join([config['directions'][id]['nickname'] for id in usr.selection]).capitalize(),
                                            "role_ids": list(usr.selection),
                                            "timecode": time()})
                f.seek(0)
                json.dump(database, f, indent=4, ensure_ascii=False)

            direction_list = ', '.join([config['directions'][id]['name'].lower() for id in usr.selection])
            # администратор, худрук и зам получают сообщения вообще обо всех заявках
            # остальные замыкающие - только если в заявке есть их направление
            # список рассылки формируется как set во избежание дублирования сообщений 
            # (из-за того, что худрук местами ещё и замыкающий) 
            spambase = {director_id(config['directions'][id]['codename']) for id in usr.selection}
            spambase.update([director_id('owner'), director_id('admin'), director_id('deputy')])
            spambase.discard(0) # для "отсутствующих" замыкающих
            for id in spambase:
                sendMessage(id, f"@id{from_id} ({usercache[from_id].name}) подал(а) заявку в: {direction_list}.")
            sendMessage(from_id, f"""
Спасибо за регистрацию! ❤️
                            
Напоследок - присоединись, пожалуйста, к чату набора:
{config['chat_url']}
                            
Это нужно сделать обязательно - в дальнейшем в нём будет размещена важная информация.
                            """, keyboards.get_final_buttons(config['chat_url']))
            usercache.pop(from_id, None)

        # === нажатие кнопки "хочу сюда!" ===
        elif (command == 'select' or sel_force_render) and 0 <= data <= dir_count:
            if not sel_force_render: usercache[from_id].selection.add(data)
            reply = "Твой выбор:\n\n{0}{1}".format(
                        '\n'.join(['· ' + config['directions'][id]['name'] for id in usercache[from_id].selection]),
                        '\n\nТы можешь указать ещё несколько направлений или закончить.\nЧтобы отменить выбор, повторно нажми на соответствующее направление в меню.'
                        if len(usercache[from_id].selection) == 1 else '')
            sendMessage(from_id, reply, keyboards.generate_dirs_keyboard(config['directions'], usercache[from_id].selection))

        # === нажатие кнопки "закончить выбор" ===
        elif command == 'finish' and len(usercache[from_id].selection) > 0:
            roles = ', '.join([config['directions'][id]['nickname'] for id in usercache[from_id].selection])
            msg = f"""
Отлично! Тво{'и роли' if len(usercache[from_id].selection) > 1 else 'я роль'} в Призме - {roles}.

Если {usercache[from_id].name} - твои настоящие фамилия и имя, то напиши, пожалуйста, своё отчество (например, Иванович).
Если это неправильно или они написаны на иностранном языке - напиши своё ФИО полностью.
            """
            sendMessage(from_id, msg, keyboards.fio_request)
            usercache[from_id].stage = 1

        # === админские команды ===
        elif from_id == config['bot_admin']: 
            if text == '/lol': # отладочное
                a = 1/0
            elif text == '/reload':
                conf = loadConfiguration()
                if conf:
                    config = conf
                    sendMessage(from_id, 'Конфигурация обновлена')
                else: sendMessage(from_id, 'Ошибка загрузки конфигурации')

        # === "олд" ===
        elif text.lower() == 'олд':
            sendMessage(from_id, f"""
Прочитай описание направлений по ссылке: {config['about_directions_url']} и определись с интересующими тебя направлениями.
                        
Затем в свободной форме напиши мне своё ФИО, номер группы (если ты учишься в Самарском университете), дату рождения (при желании) и направления, в которых ты хочешь участвовать.
                        """, '{"buttons": []}')
            # секретная пятая стадия
            usercache[from_id].stage = 5

        # === движение по стадиям регистрации ===
        elif command in ('none', 'skip'):
            # обработка О/ФИО, переход на ввод номера группы
            if usercache[from_id].stage == 1:
                if command != 'skip':
                    # если в введённом тексте есть пробелы, считаем, что ввели больше, чем отчество
                    # и в таком случае заменяем вообще всё изначальное ФИ на введённый текст
                    if text.count(' ') > 0:
                        usercache[from_id].name = text
                    # если пробелов нет, значит, вероятно, ввели одно только отчество
                    # поэтому просто дополняем ВКшное ФИ введённым текстом
                    else:
                        usercache[from_id].name += ' ' + text
                # и потом просим у клиента номер группы
                sendMessage(from_id, 'Теперь напиши номер своей группы (например, 6411-110501D).\n\n‼️ Пропусти этот шаг, если ты не студент Самарского университета.', keyboards.group_no)
                usercache[from_id].stage = 2

            # обработка номера группы, переход на стадию ввода даты рождения
            elif usercache[from_id].stage == 2:
                usercache[from_id].group_no = text if command != 'skip' else '-'
                # попытаться извлечь дату рождения со страницы ВК
                # если она не скрыта, то появится кнопка для автоматического ввода
                user = vk.users.get(user_ids=from_id,fields='bdate',lang=0)[0]
                sendMessage(from_id, 'Мы в Призме ценим каждого и не оставим без внимания твой День Рождения.\nНапиши день и месяц своего рождения, чтобы мы знали, когда тебя поздравлять!',
                            keyboards.get_bday_buttons(user.get('bdate', '')))
                
                usercache[from_id].stage = 3

            # запрос на сверку окончательных данных
            elif usercache[from_id].stage == 3:
                usercache[from_id].birthday = text if command != 'skip' else '-'
                sendMessage(from_id, f"""
Давай всё сверим:

· ФИО: {usercache[from_id].name}
· Роли: {', '.join([config['directions'][id]['nickname'] for id in usercache[from_id].selection])}
· Группа: {usercache[from_id].group_no}
· ДР: {usercache[from_id].birthday}

Если всё правильно, нажми кнопку "Подтвердить".
Если у тебя появился вопрос - напиши его сейчас, и мы ответим как можно скорее.
""", keyboards.get_confirm_buttons())
                usercache[from_id].stage = 4

            # обработка ручной подачи заявки
            elif usercache[from_id].stage == 5:
                with open('userdata/registered.json', 'r+', encoding='utf-8') as f:
                    database = json.load(f)
                    database['manual'].append({"name": usercache[from_id].vkname,
                                                "text": text,
                                                "vk": 'https://vk.com/id' + str(from_id),
                                                "timecode": time()})
                    f.seek(0)
                    json.dump(database, f, indent=4, ensure_ascii=False)
                
                spambase = {director_id('owner'), director_id('admin'), director_id('deputy')}
                for id in spambase:
                    sendMessage(id, f"@id{from_id} ({usercache[from_id].name}) подал(а) заявку вручную:\n{text}")
                sendMessage(from_id, f"""
Информацию приняли, спасибо! ❤️
Мы обработаем твою заявку вручную.
                            
Ты уже сейчас можешь присоединиться к чату набора:
{config['chat_url']}
                            
Это нужно сделать обязательно - в дальнейшем в нём будет размещена важная информация.
                            """)
                usercache.pop(from_id, None)
try:
    # главный цикл бота (приём и обработка сообщений)
    print('[INFO] Bot is started.')
    logger.info("Bot is started.")
    while True:
        try:
            receiver.do(processMessage)
        except Exception as e:
            # отлов ошибок без аварийного завершения работы
            print("[ERROR] Something went wrong!!!", e)
            sendMessage(config['bot_admin'], "боту плохо, посмотри логи...\n" + str(e))
            logger.error(e, exc_info=True)
except KeyboardInterrupt:
    # обработка команды завершения работы
    receiver.saveSession()
    print('Stopping.')
    logger.info("Shutting down.")
    exit(0)