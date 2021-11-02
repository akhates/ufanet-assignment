# coding=utf-8
import sys
import os
import json
from bot import *

__author__ = 'earedcloud'

if __name__ == '__main__':
    try:
        # Получаем конфиг
        with open("settings.json") as json_file:
            config = json.load(json_file)
        bot_api_token = config['TELEGRAM_BOT_HTTP_API_TOKEN']
        request_timeout = config['REQUEST_TIMEOUT']
        db_host = config['MYSQL_SERVER_HOST']
        db_port = config['MYSQL_SERVER_PORT']
        db_user = config['MYSQL_SERVER_USERNAME']
        db_password = config['MYSQL_SERVER_PASSWORD']
        db_schema = config['MYSQL_SERVER_SCHEMA_NAME']

        # Создаем экземпляр класса бота и передаем в конструктор параметры из конфига
        bot = TelegramBot(bot_api_token, request_timeout, db_host, db_user, db_password, db_schema)
        bot.start_long_polling()

    except StandardError as err:
        print str(err)
        raise
