import telebot
from telebot import types
import os
import time
import logging
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from config import *

bot = telebot.TeleBot(token=BOT_TOKEN)
server = Flask(__name__)
server.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
db = SQLAlchemy(server)
logger = telebot.logger
logger.setLevel(logging.DEBUG)


class Topic(db.Model):
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"),primary_key=True)
    name = db.Column(db.String(80))


class Question(db.Model):
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"),primary_key=True)
    topic = db.Column(db.Integer)
    question = db.Column(db.String(80))


class Answer(db.Model):
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    question = db.Column(db.Integer)
    db.answer = db.Column(db.String(80))
    db.correct = db.Column(db.Boolean)


class Session(db.Model):
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    user = db.Column(db.Integer)
    passed_questions = db.Column(db.Integer)
    current_question = db.Column(db.Integer)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton('a')
    itembtn2 = types.KeyboardButton('v')
    itembtn3 = types.KeyboardButton('d')
    markup.add(itembtn1, itembtn2, itembtn3)
    bot.send_message(message.chat_id, "Choose one letter:", reply_markup=markup)


@server.route(f"/{BOT_ENDPOINT}", methods=['POST'])
def redirect_message():
    json = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json)
    bot.process_new_updates([update])
    return "ok", 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))