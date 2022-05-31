import telebot
import time

bot_token = "5520828799:AAHVMscC9OJuKIKS1IxEAsVHxWFkui6E-G8"

bot = telebot.TeleBot(token=bot_token)

@bot.message_handlers(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "welcome")

bot.polling()