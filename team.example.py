#############################################
# файл является примером заполнения team.py #
#  имена и ID заполнены случайным образом   #
#############################################

greeting = """
Выбери направление в списке, чтобы узнать о нём больше и подать заявку!
"""

choose = """
Отлично! Твой выбор - {0}.

Если {1} - твои настоящие имя и фамилия, то напиши, пожалуйста, своё отчество (например: Иванович).
Если это неправильно или они написаны на иностранном языке - напиши полностью своё настоящее ФИО (например: Иванов Иван Иванович или просто Иванов Иван, если нет отчества).
"""

group_request = """
Теперь напиши номер своей группы (например: 1111-111111D).
"""

thanks = """
Спасибо за регистрацию! ❤

Напоследок - присоединись, пожалуйста, к беседе набора: {0}
Это важно, поскольку по окончании набора в беседе будут размещены приглашения в наши общие чаты.
"""

directorate = {
    "music": [1111111111, "Имя Фамилия"], # музыкальное направление
    "scenario": [222222222222, "Имя Фамилия"], # сценарное направление
    "decorator": [333333333, "Имя Фамилия"], # декораторское направление
    "dance": [0], # заглушка (танцевальное направление)
    "inform": [0], # заглушка (информационное направление)
    "actor": [4444444444, "Имя Фамилия"], # актёрское направление
    "mto": [5555, "Имя Фамилия"], # МТО
    "tech": [7777, "Имя Фамилия"], # техническая служба
    "admin": [7777777777, "Имя Фамилия"], # администратор
    "owner": [888888888888, "Имя Фамилия"] # худрук-основатель
}

directions = [
    {
        "name": "Музыкальное направление",
        "description": "описание музыкалки",
        "codename": "music", 
        "emoji": "🎼"
    },
    {
        "name": "Сценарное направление",
        "description": "описание сценарки",
        "codename": "scenario", 
        "emoji": "✍️"
    },
    {
        "name": "Декораторское направление",
        "description": "описание декораторки",
        "codename": "decorator",
        "emoji": "🎡"
    },
    {
        "name": "Танцевальное направление",
        "description": "описание танцорки",
        "codename": "dance",
        "emoji": "💃"
    },
    {
        "name": "Информационная служба",
        "description": "описание информа",
        "codename": "inform",
        "emoji": "📰"
    },
    {
        "name": "Актёрское направление",
        "description": "описание актёрки",
        "codename": "actor",
        "emoji": "🎭"
    },
    {
        "name": "Материально-техническое обеспечение",
        "description": """<описание МТО>
        ♫ Never gonna give you up ♫
        ♫ Never gonna let you down ♫
        ♫ Never gonna run around and desert you ♫
        ♫ Never gonna make you cry ♫
        ♫ Never gonna say goodbye ♫
        ♫ Never gonna tell a lie and hurt you ♫
        """,
        "codename": "mto",
        "emoji": "👷"
    },
    {
        "name": "Техническая служба",
        "description": "описание техов",
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