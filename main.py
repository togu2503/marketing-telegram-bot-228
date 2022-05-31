import telebot
import json
import random
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
    answer = db.Column(db.String(80))
    correct = db.Column(db.Boolean)


class Session(db.Model):
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    user = db.Column(db.Integer)
    passed_questions = db.Column(db.Integer)
    current_question = db.Column(db.Integer)
    mark = db.Column(db.Integer)


@bot.message_handler(commands=['menu'])
def show_current_menu(message):
    inline_markup = types.InlineKeyboardMarkup()
    inlinebtn1 = types.InlineKeyboardButton(text="Start Quiz")
    inlinebtn1.callback_data = "/start_quiz"
    inline_markup.add(inlinebtn1)
    bot.send_message(message.chat.id, text="Choose one:", reply_markup=inline_markup)


@bot.message_handler(commands=['stop'])
def stop_quiz(message):

    session = Session.query.filter_by(user=message.from_user.id).first()
    if session:
        db.session.delete(session)
        db.session.commit()
        bot.send_message(message.chat.id, text="Quiz has been canceled")
        return

    bot.send_message(message.chat.id, text="You have not started quiz yet")


@bot.message_handler(commands=['start'])
def start_quiz_menu(message):
    session = Session.query.filter_by(user=message.from_user.id).first()

    if session:
        bot.send_message(message.chat.id, text="You have already started quiz")
        return

    inline_markup = types.InlineKeyboardMarkup()
    topics = Topic.query.all()

    for topic in topics:
        topicbtn = types.InlineKeyboardButton(topic.name)
        topicbtn.callback_data = '{"quiz_id": ' + str(topic.id)+"}"
        inline_markup.add(topicbtn)

    bot.send_message(message.chat.id, text="Choose quiz:", reply_markup=inline_markup)


def is_answer_callback(callback):
    data = json.loads(callback.data)

    if 'answer_id' in data:
        return True

    return False


def create_answers_buttons(question_id):
    answers = Answer.query.filter_by(question=question_id).all()

    inline_markup = types.InlineKeyboardMarkup()
    for answer in answers:
        inline_btn = types.InlineKeyboardButton(answer.answer)
        inline_btn.callback_data = '{"answer_id":'+str(answer.id)+"}";
        inline_markup.add(inline_btn)

    return inline_markup


def send_question(chat_id, question, num):
    inline_markup = create_answers_buttons(question.id)
    num += 1
    bot.send_message(chat_id, text="№" + str(num) + ": " + question.question, reply_markup=inline_markup)


def quiz_finished(session, chat_id):
    bot.send_message(chat_id, text="You finished quiz! ")
    bot.send_message(chat_id, text="Your score: " + str(session.mark)+" / " + str(session.passed_questions))
    db.session.delete(session)
    db.session.commit()


@bot.callback_query_handler(func=lambda call: is_answer_callback(call))
def user_answered(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

    data = json.loads(call.data)
    answer_id = data['answer_id']

    answer = Answer.query.filter_by(id=answer_id).first()

    if not answer:
        bot.send_message(call.message.chat.id, text="Something wrong =(")

    session = Session.query.filter_by(user=call.from_user.id).first()

    if not session:
        return

    if answer.correct:
        session.mark += 1

    session.passed_questions += 1

    if session.passed_questions >= TESTS_AMOUNT:
        quiz_finished(session, call.from_user.id)
        return

    questions = Question.query.all()
    question = random.choice(questions)
    session.current_question = question.id
    db.session.commit()

    send_question(call.message.chat.id, question, session.passed_questions)


def is_topic_callback(callback):
    data = json.loads(callback.data)

    if 'quiz_id' in data:
        return True

    return False


@bot.callback_query_handler(func=lambda call: is_topic_callback(call))
def create_session(call):
    data = json.loads(call.data)
    quiz_id = int(data['quiz_id'])

    topic = Topic.query.filter_by(id=quiz_id).first()

    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, text="Your topic: "+topic.name)

    questions = Question.query.filter_by(topic=quiz_id).all()
    if len(questions):
        question = random.choice(questions)

        session = Session(user=call.from_user.id, passed_questions=0, current_question=question.id, mark=0)
        db.session.add(session)
        db.session.commit()

        send_question(call.message.chat.id, question, session.passed_questions)


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