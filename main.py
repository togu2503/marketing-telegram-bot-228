import telebot
import os
import time
from flask import Flask, request
from config import *

bot = telebot.TeleBot(token=BOT_TOKEN)
server = Flask(__name__)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Welcome with webhook!')


@server.route(f"/{}", methods=['POST'])
def redirect_message():
    json = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json)
    bot.process_new_updates([update])
    return "ok", 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))