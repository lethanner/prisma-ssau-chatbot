from requests import Session
from logging import Logger
from os.path import exists
from time import sleep
import json

class LongPoll:
    def __init__(self, group_id: int, vk, logger: Logger):
        self.group_id = group_id
        self.vk = vk
        self.logger = logger
        self.connection = Session()
        
        if exists('userdata/longpoll.json'):
            with open('userdata/longpoll.json', 'r', encoding='utf-8') as f:
                print('[SYSTEM] Loading longpoll.json')
                self.config = json.load(f)
        else:
            self.__updateSession()

    def saveSession(self):
        print("[SYSTEM] Saving longpoll.json...", end='')
        with open('userdata/longpoll.json', 'w+', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
        print("done.")
        pass

    def __updateSession(self):
        try:
            self.config = self.vk.groups.getLongPollServer(group_id=self.group_id)
            self.logger.debug("Got new Long Poll server config")
            self.logger.debug(self.config)
            self.saveSession()
        except Exception as e:
            self.logger.error(e, exc_info=True)
            print("[ERROR] Failed to get Long Poll server config!", e)

    def do(self, callback):
        try:
            self.events = self.connection.get(self.config['server'],
                                                params={'act': 'a_check',
                                                        'key': self.config['key'],
                                                        'ts': self.config['ts'],
                                                        'wait': 25}, timeout=30).json()
            self.logger.debug(self.events)
            error = self.events.get('failed')
            if error in (2, 3):
                self.__updateSession()
                return

            self.config['ts'] = self.events['ts']

        except Exception as e:
            print("[ERROR] Long Poll error!!!!!")
            self.logger.error("Fatal LongPoll error!")
            self.logger.error(e, exc_info=True)
            print("[INFO] Waiting 30 seconds")
            sleep(30)
            #__updateSession()
            return
        
        callback(self.events)