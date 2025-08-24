import json

# месяцы рождения
bmonths = ('января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря')

# генератор клавиатуры со списком направлений
# (с выделением выбранных зеленым цветом)
# (и автодобавлением кнопки завершения выбора)
def generate_dirs_keyboard(directions, selected: set = set()):
    obj = {"one_time": False, "buttons": []}
    if len(selected) > 0:
        obj["buttons"].append([{"action": {"type": "text", "payload": '{"command": "finish"}', "label": "Закончить выбор"}, "color": "primary"}])
    
    for index, dir in enumerate(directions):
        payload = '{{"command": "{0}", "data": "{1}"}}'.format('deselect' if index in selected else 'descr', str(index))
        obj["buttons"].append([{
            "action": {
                "type": "text",
                "payload": payload,
                "label": dir["emoji"] + ' ' + dir["name"]
            },
            "color": "positive" if index in selected else "secondary"
        }])

    return json.dumps(obj)

# генератор кнопки выбора направления
def get_sel_button(id: int):
    return json.dumps({
            "inline": True,
            "buttons": [[{
                "action": {
                    "type": "callback",
                    "payload": '{"command": "select", "data": ' + str(id) + '}',
                    "label": "Хочу сюда!"
                },
                "color": "positive"
            }]]})

def get_confirm_buttons():
    return json.dumps({
                "buttons": [[{
                    "action": {
                        "type": "text",
                        "payload": '{"command": "submit"}',
                        "label": "Подтвердить"
                    }
                }],[{
                    "action": {
                        "type": "text",
                        "payload": '{"command": "again"}',
                        "label": "Начать заново"
                    },
                    "color": "negative"
                }]]})

def get_final_buttons(url: str):
    return json.dumps({
                "buttons": [[{
                    "action": {
                        "type": "open_link",
                        "link": url,
                        "label": "Присоединиться к чату"
                    }
                }],[{
                    "action": {
                        "type": "text",
                        "payload": '{"command": "start"}',
                        "label": "Подать ещё одну заявку"
                    },
                    "color": "secondary"
                }]]})

# кнопки в процессе ввода О/ФИО
fio_request = json.dumps({
                "one_time": True,
                "buttons": [[{
                    "action": {
                        "type": "text",
                        "payload": '{"command": "skip"}',
                        "label": "Имя верное, отчества нет"
                    },
                    "color": "secondary"
                }],[{
                    "action": {
                        "type": "text",
                        "payload": '{"command": "again"}',
                        "label": "Начать заново"
                    },
                    "color": "negative"
                }]]})

# кнопки в процессе ввода номера группы
group_no = json.dumps({
                "one_time": True,
                "buttons": [[{
                    "action": {
                        "type": "text",
                        "payload": '{"command": "skip"}',
                        "label": "Пропустить этот шаг"
                    },
                    "color": "secondary"
                }],[{
                    "action": {
                        "type": "text",
                        "payload": '{"command": "again"}',
                        "label": "Начать заново"
                    },
                    "color": "negative"
                }]]})

def get_bday_buttons(date: str):
    if date:
        # формат "3.6" представляем как "3 июня"
        bdate = date.split('.')
        bdate = bdate[0] + ' ' + bmonths[int(bdate[1]) - 1]

        return json.dumps({
                "one_time": True,
                "buttons": [[{
                    "action": {
                        "type": "text",
                        "label": bdate,
                        "payload": '{"stats": "dr_shortcut_used",'
                                            '"command": "none"}',
                    },
                    "color": "primary"
                }],[{
                    "action": {
                        "type": "text",
                        "payload": '{"command": "skip"}',
                        "label": "Не указывать"
                    },
                    "color": "secondary"
                }],[{
                    "action": {
                        "type": "text",
                        "payload": '{"command": "again"}',
                        "label": "Начать заново"
                    },
                    "color": "negative"
                }]]})
    
    # если получить дату из ВК не удалось, возвращаем те же
    # кнопки, что были при указании номера группы
    else:
        return group_no
    
    
# кнопка повторной подачи заявки (полностью аналогична кнопке "начать")
# restart = json.dumps({
#             "one_time": True,
#             "buttons": [[{
#                 "action": {
#                     "type": "text",
#                     "payload": '{"command": "start"}',
#                     "label": "Подать ещё одну заявку"
#                 }
#             }]]})