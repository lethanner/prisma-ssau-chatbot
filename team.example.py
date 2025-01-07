#############################################
# файл является примером заполнения team.py #
#  имена и ID заполнены случайным образом   #
#############################################

greeting = """
текст приветствия
"""

choose = """
Отлично! Твой выбор - {0}.

Если {1} - твои настоящие имя и фамилия, то напиши, пожалуйста, своё отчество (например: Иванович).
Если это неправильно или они написаны на иностранном языке - напиши полностью своё настоящее ФИО (например: Иванов Иван Иванович или просто Иванов Иван, если нет отчества).
"""

group_request = """
Теперь напиши номер своей группы (например, 1111-111111D).
"""

thanks = """
Спасибо за регистрацию! ❤
Ближе к концу набора с тобой свяжется наш администратор или замыкающий выбранного тобой направления.
"""

directorate = {
    "music": [1111111, "Имя1 Фамилия1"], # музыкальное направление
    "scenario": [2111122, "Имя2 Фамилия2"], # сценарное направление
    "decorator": [5424524, "Имя3 Фамилия3"], # декораторское направление
    "dance": [0], # заглушка (танцевальное направление)
    "inform": [0], # заглушка (информационное направление)
    "mto": [2341235, "Имя4 Фамилия4"], # МТО
    "tech": [7467858, "Имя5 Фамилия5"], # техническая служба
    "admin": [5245634, "Имя6 Фамилия6"], # администратор
    "owner": [5123524, "Имя7 Фамилия7"] # худрук-основатель
}

directions = [
    {
        "name": "Музыкальное направление",
        "description": "тут описание музыкалки",
        "codename": "music", 
        "emoji": "🎼"
    },
    {
        "name": "Сценарное направление",
        "description": "тут описание сценарки",
        "codename": "scenario", 
        "emoji": "✍️"
    },
    {
        "name": "Декораторское направление",
        "description": "тут описание декораторки",
        "codename": "decorator",
        "emoji": "🎡"
    },
    {
        "name": "Танцевальное направление",
        "description": "тут описание танцевалки",
        "codename": "dance",
        "emoji": "💃"
    },
    {
        "name": "Информационная служба",
        "description": "тут описание информа",
        "codename": "inform",
        "emoji": "📰"
    },
    {
        "name": "Материально-техническое обеспечение",
        "description": "тут описание МТО",
        "codename": "mto",
        "emoji": "👷"
    },
    {
        "name": "Техническая служба",
        "description": "тут описание техов",
        "codename": "tech",
        "emoji": "🎛"
    },
]

dir_count = len(directions)

def generate_keyboard():
    obj = {"one_time": False, "buttons": []}
    for index, dir in enumerate(directions):
        obj["buttons"].append([{
            "action": {
                "type": "text",
                "payload": '{"command": "descr", "data": ' + str(index) + '}',
                "label": dir["emoji"] + ' ' + dir["name"]
            }
        }])

    return obj

def get_director(id: int):
    return directorate[directions[id]['codename']]

def dir_description(id: int):
    msg = directions[id]['description']
    # если замыкающий направления вообще существует, добавим о нём информацию
    if get_director(id)[0] > 0:
        msg += "\r\n\r\nЗамыкающий направления - [id{0}|{1}].".format(*get_director(id))
    else:
        msg += "\r\n\r\nВременный замыкающий направления - [id{0}|{1}].".format(*directorate['owner'])
    
    return msg

def choose_msg(id: int, fi: str):
    return choose.format(directions[id]['name'].lower(), fi)