import os
import telebot
import google.generativeai as genai
from telebot import types

# --- الإعدادات المطورة (Auto-Detect Key) ---
TOKEN = os.getenv("BOT_TOKEN")
# سيحاول الكود قراءة المفتاح بكل الأسماء المحتملة لضمان العمل
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_KEY")

ADMIN_ID = 8336468616 
bot = telebot.TeleBot(TOKEN)

# التأقق من وجود المفتاح قبل التشغيل
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    print("⚠️ Warning: Gemini API Key not found!")
    

# --- فلتر الكلمات (Shield) ---
BANNED_WORDS = ["كلمة1", "كلمة2"]

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 تم تفعيل العقل الاصطناعي بنجاح! أنا الآن جاهز للإجابة على أي سؤال بذكاء خارق.")

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "🛠️ أهلاً بك يا مطوري في لوحة التحكم المركزية.")

@bot.message_handler(func=lambda message: True)
def ai_logic(message):
    # حماية من الكلمات المسيئة
    if any(word in message.text.lower() for word in BANNED_WORDS):
        bot.delete_message(message.chat.id, message.message_id)
        return

    # إرسال طلب للمحرك الذكي
    try:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "📡 عذراً، المحرك الذكي بانتظار مفتاح الـ API للعمل.")

bot.polling(none_stop=True)

