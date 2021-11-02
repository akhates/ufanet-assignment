# coding=utf-8
from datetime import datetime
import re
import urllib
import requests
import json
import logging
import logging.handlers
from time import sleep
import mysql.connector
import unittest


__author__ = 'earedcloud'


class TelegramBot:
    def __init__(self, bot_api_token, request_timeout, db_host, db_user, db_password, db_schema):
        self.url = "https://api.telegram.org/bot{}".format(bot_api_token)
        self.request_timeout = request_timeout
        self.db_connection = mysql.connector.connect(host=db_host, user=db_user, passwd=db_password, database=db_schema,
                                                     auth_plugin='mysql_native_password')
        self.cursor = self.db_connection.cursor(buffered=True)
        self.logger = logging.getLogger('logger')

    # Method for making request and getting json response
    def make_request(self, url):
        r = requests.get(url, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        content = json.loads(r.content)
        return content

    # Method to get updates from telegram's api getUpdates endpoint
    def get_updates(self, offset=None):
        url = self.url + "/getUpdates?timeout={}".format(self.request_timeout)
        if offset:
            url += "&offset={}".format(offset)
        response = self.make_request(url)
        return response

    # Method to get latest update id to use as an offset
    def get_last_update_id(self, updates):
        update_ids = []
        for update in updates["result"]:
            update_ids.append(int(update["update_id"]))
        return max(update_ids)

    # Method for handling commands
    def respond_to_updates(self, updates):
        for update in updates["result"]:
            if update.get("message") is None:
                return
            if update.get("message", {}).get("text") is None:
                return

            text = update["message"]["text"]
            command = text.split()[0]
            chat_id = update["message"]["chat"]["id"]
            self.logger.info(u"requesting [{}] on behalf of [chat_id={}]".format(text, chat_id))

            if command == "/test":
                text = u"test response"
                self.send_message(text, chat_id)
                return

            elif command == "/start":
                self.start(chat_id)
                self.send_message(u"Телеграм бот для тестового задания. Напишите /help для списка команд.", chat_id)
                return

            elif command == "/help":
                self.send_message(u"/start сохраняет telegram id пользователя в базу и присваивает пользователю id.\n"
                                  u"/help возвращает список команд.\n"
                                  u"/write записывает сообщение после команды в таблицу messages, присваивает ему id, "
                                  u"запоминает, что данное сообщение является последним для данного пользователя, "
                                  u"выводит после исполнения команды текст 'заметка <id> сохранена'.\n"
                                  u"/read_last выводит последнее сообщение данного пользователя.\n"
                                  u"/read <id> выводит поле сообщение с указанным id. Если такового нет, "
                                  u"то выводит текст 'заметка <id> не найдена', "
                                  u"либо 'заметка <id> принадлежит другому пользователю', "
                                  u"если была попытка прочитать заметку другого пользователя.\n"
                                  u"/read_all выводит все заметки текущего пользователя бота по порядку "
                                  u"от самого старого до самого нового.\n"
                                  u"/read_tag <tag> выводит все заметки по указанному тэгу в сообщении "
                                  u"(в одном сообщении тэгов может быть несколько, например "
                                  u"'Компания #Уфанет предупреждает, что вещатель проводит работы "
                                  u"на следующих каналах: #Россия1 и #СТС').\n"
                                  u"/tag <tag_1>,<tag_2>...<tag_n> выводит описание введенных тэгов.\n"
                                  u"/tag_all выводит описание всех тэгов.", chat_id)
                return

            elif command == "/write":
                self.write(chat_id, text[6:].strip())
                return

            elif command == "/read_last":
                self.read_last(chat_id)
                return

            elif command == "/read":
                self.read(chat_id, text[5:].strip())
                return

            elif command == "/read_all":
                self.read_all(chat_id)
                return

            elif command == "/read_tag":
                self.read_tag(chat_id, text[9:].strip())
                return

            elif command == "/tag":
                self.tag(chat_id, text[4:].strip())
                return

            elif command == "/tag_all":
                self.tag_all(chat_id)
                return

            elif command[0] == "/":
                self.send_message(u"Команда не найдена. Напишите /help для списка команд.", chat_id)
            return

    # Method for sending messages to target chat_id
    def send_message(self, text, chat_id):
        text = urllib.quote_plus(text.encode("utf8"))
        url = self.url + "/sendMessage?text={}&chat_id={}".format(text, chat_id)
        self.make_request(url.decode("utf8"))

    # Method for /start command, saves chat_id into database if doesn't exists
    def start(self, chat_id):
        self.cursor.execute(u"SELECT COUNT(1) FROM users WHERE chat_id = '{}'".format(chat_id))
        if self.cursor.fetchone()[0]:
            # chat_id существует
            return
        else:
            # chat_id не существует, сохраняем
            self.cursor.execute(u"INSERT INTO users (chat_id, date_joined) VALUES (%s, %s)", (chat_id, datetime.now()))
            self.db_connection.commit()

    # Method for /write command, saves message from user
    def write(self, chat_id, message):
        try:
            self.cursor.execute(u"INSERT INTO messages (chat_id, text, datetime) VALUES (%s, %s, %s)", (chat_id, message, datetime.now()))
            self.db_connection.commit()
        except mysql.connector.errors.DataError:
            self.send_message(u"Текст сообщения слишком длинный", chat_id)
            return

        self.cursor.execute(u"SELECT MAX(id) FROM messages WHERE chat_id = '%s'", (chat_id,))
        message_id = self.cursor.fetchone()[0]

        self.send_message(u"Заметка #{} сохранена.".format(message_id), chat_id)

    # Method for /read_last command, returning last saved message
    def read_last(self, chat_id):
        self.cursor.execute(u"SELECT MAX(id), text FROM messages WHERE chat_id = '%s'", (chat_id,))
        message = self.cursor.fetchone()
        message_id = message[0]
        message_text = message[1]

        self.send_message(u"Заметка #{}: {}".format(message_id, message_text), chat_id)

    # Method for /read_id command, returning target saved message if possible
    def read(self, chat_id, message_id):
        # checking if message exists
        self.cursor.execute(u"SELECT COUNT(1) FROM messages WHERE id = '{}'".format(message_id))
        if not self.cursor.fetchone()[0]:
            self.send_message(u"Заметка #{} не найдена.".format(message_id), chat_id)
            return

        # checking ownership
        self.cursor.execute(u"SELECT COUNT(1) FROM messages WHERE id = '{}' AND chat_id = '{}'".format(message_id, chat_id))
        if not self.cursor.fetchone()[0]:
            self.send_message(u"Заметка #{} принадлежит другому пользователю.".format(message_id), chat_id)
            return

        # returning message
        self.cursor.execute(u"SELECT text FROM messages WHERE id = '{}' AND chat_id = '{}' ORDER BY id DESC".format(message_id, chat_id))
        message_text = self.cursor.fetchone()[0]
        self.send_message(u"Заметка #{}: {}".format(message_id, message_text), chat_id)

    # Method for /read_all, getting all saved messages
    def read_all(self, chat_id):
        self.cursor.execute(u"SELECT id, text FROM messages WHERE chat_id = '%s' ORDER BY id", (chat_id,))
        messages = self.cursor.fetchall()
        if len(messages) == 0:
            self.send_message(u"У вас нет ни одной заметки.", chat_id)
            return
        for message in messages:
            self.send_message(u"Заметка #{}: {}".format(message[0], message[1]), chat_id)

    # Method for /read_tag, returns all messages that has specified tag inside in it
    def read_tag(self, chat_id, tag):
        self.cursor.execute(u"SELECT id, text FROM messages WHERE messages.`text` LIKE '%{}%' AND chat_id = '{}' COLLATE utf8_general_ci ORDER BY id".format(tag, chat_id).encode('utf8'))
        messages = self.cursor.fetchall()
        if len(messages) == 0:
            self.send_message(u"Нет сообщений имеющих данный тег", chat_id)
            return
        for message in messages:
            self.send_message(u"Заметка #{}: {}".format(message[0], message[1]), chat_id)

    # Method for /tag <id>, returns descriptions of specified tags
    def tag(self, chat_id, tags):
        # use regular expression to remove all commas
        tags = re.sub(",", "", tags)

        # split string by whitespaces into array
        tags = tags.split()
        if len(tags) == 0:
            return
        for tag in tags:
            if tag[0] != "#":  # check if hashtag
                continue
            self.cursor.execute(u"SELECT description FROM tags WHERE name = '{}'".format(tag).encode('utf8'))
            query = self.cursor.fetchone()
            self.send_message(u"Тэг: {}: {}".format(tag, query[1]), chat_id)

    # Method for /tag_all, returns descriptions of all tags
    def tag_all(self, chat_id):
        self.cursor.execute(u"SELECT name, description FROM tags")
        tags = self.cursor.fetchall()
        if len(tags) == 0:
            return
        for tag in tags:
            self.send_message(u"Тэг: {}: {}".format(tag[0], tag[1]), chat_id)

    # Logging settings
    def init_logging(self):
        self.logger.setLevel(logging.DEBUG)

        # logging format
        formatter = logging.Formatter('[%(levelname)s] - %(asctime)s - %(message)s')

        # handler for writing into file
        now = datetime.now()
        fh = logging.FileHandler("output_log_" + now.strftime("%d-%m-%Y_%H-%M-%S") + '.log', mode='w', encoding='utf-8')
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        # handler for writing into console
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    # Long polling for telegram's API
    def start_long_polling(self):
        last_update_id = None

        # initializing logging
        self.init_logging()
        self.logger.info("Starting application...")

        try:
            while True:
                # request timeout specified in settings.json
                sleep(self.request_timeout)

                updates = self.get_updates(last_update_id)
                if updates is None:
                    return
                elif len(updates["result"]) > 0:
                    last_update_id = self.get_last_update_id(updates) + 1
                    self.respond_to_updates(updates)
        except KeyboardInterrupt:
            self.logger.info("Closing application...")
