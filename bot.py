import telebot
import os
from dotenv import load_dotenv

# تحميل المتغيرات السرية
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "⚡ تم تفعيل السورس بنجاح على نظام The Architect.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"أرسلت: {message.text}")

if __name__ == "__main__":
    print("--- البوت قيد العمل الآن ---")
    bot.infinity_polling()
  
