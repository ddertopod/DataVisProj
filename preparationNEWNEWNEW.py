import telebot
import os
from dotenv import load_dotenv

load_dotenv()

API = os.getenv("TELEAPI")
bot = telebot.TeleBot(API)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
  bot.send_message(message.from_user.id, message.text)


bot.polling(none_stop=True, interval=0) 