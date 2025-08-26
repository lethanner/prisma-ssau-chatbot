import xlsxwriter
import json
import vk
#from sys import argv
from os.path import dirname
from datetime import datetime

now = datetime.now()

#infile = argv[1]
infile = 'userdata/registered.json'
outfile = dirname(infile) + now.strftime("/%Y%m%d_%H%M%S.xlsx")

chat_members = []
try:
    with open('userdata/config.json', 'r', encoding='utf-8') as f:
        conf = json.load(f)

        vk = vk.API(access_token=conf['auth_token'],v=5.199)
        chat_id = 2000000000 + conf['group_id_in_chat']

        members = vk.messages.getConversationMembers(peer_id=chat_id)['profiles']
        chat_members = [profile['id'] for profile in members]

        print(f'Загружен список участников чата ({len(chat_members)})')
except Exception as e:
    print(f'{e}\n\033[33mВНИМАНИЕ:\033[0m Не удалось загрузить список участников чата. Таблица будет сгенерирована без отсеивания.\n')
    pass

try:
    with open(infile, 'r', encoding='utf-8') as f:
        data = json.load(f)
        newbies = data['newbies']
        print(f'Загружено {len(newbies)} заявок')

        workbook = xlsxwriter.Workbook(outfile)
        worksheet = workbook.add_worksheet()
        
        header = workbook.add_format({'bold': True})
        red = workbook.add_format({'bg_color': '#FF0000'})
        unnecessary = workbook.add_format({'bg_color': '#CCCCCC'})

        # заголовок таблицы
        for i, text in enumerate(('Фамилия, имя, отчество', 'Род деятельности', 'Номер группы',
                                  'День рождения', 'Страница ВК', 'Время регистрации')):
            worksheet.write(0, i, text, header)
        
        # новички
        retired_list = []
        new_count = 0; row = 1

        keys = ('name', 'roles', 'group', 'birthday', 'vk')
        for idx, newbie in enumerate(newbies):
            if not chat_members or int(newbie['vk'][17:]) in chat_members:
                new_count += 1
                print(f"[\033[32m+\033[0m] {newbie['name']}")
            else:
                retired_list.append(idx)
                print(f"[\033[31m-\033[0m] {newbie['name']}")
                continue

            for col, key in enumerate(keys):
                worksheet.write(row, col, newbie[key])
            worksheet.write(row, 5, datetime.fromtimestamp(newbie['timecode'])
                            .strftime('%Y-%m-%d %H:%M:%S'))
        
            row += 1

        # недостающие новички
        for retired in retired_list:
            ret = newbies[retired]

            for col, key in enumerate(keys):
                worksheet.write(row, col, ret[key], red)
            worksheet.write(row, 5, datetime.fromtimestamp(ret['timecode'])
                            .strftime('%Y-%m-%d %H:%M:%S'), red)
            
            row += 1

        print(f'\nПрисоединились: {new_count}\nНе найдены в чате: {len(retired_list)}\n')

        #worksheet.set_column('E:F', None, unnecessary)
        worksheet.autofit()
        workbook.close()
        print(f'Таблица сгенерирована: {outfile}')

except FileNotFoundError:
    print(f'Файл {infile} не найден')
except json.JSONDecodeError:
    print(f'Файл {infile} повреждён')
#except Exception as e:
#    print('Ошибка:', e)