import os
import telebot
from telebot import types

# --- الإعدادات المركزية ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8336468616 
bot = telebot.TeleBot(TOKEN)

# --- قاعدة بيانات الردود العادية (حسب الكلمات المفتاحية) ---
RESPONSES = {
    "ar": {
        "مرحبا": "أهلاً بك أيها المستخدم! كيف يمكنني مساعدتك اليوم؟ 😊",
        "من انت": "أنا بوت الخدمة التلقائي، أعمل بكفاءة عالية لخدمتك.",
        "اوامر": "الأوامر المتاحة: /start, /admin (للمطور فقط)",
        "شكرا": "على الرحب والسعة! أنا هنا دائماً للمساعدة."
    },
    "en": {
        "hello": "Hello! How can I help you today? 😊",
        "who are you": "I am an automated service bot, here to help you.",
        "commands": "Available commands: /start, /admin (for developers)",
        "thanks": "You're welcome! I'm always here to help."
    }
}

# --- ميزة الحماية (فلتر الكلمات) ---
BANNED_WORDS = ["كلمة_مسيئة1", "كلمة_مسيئة2"]

@bot.message_handler(commands=['start'])
def start(message):
    lang = "ar" if message.from_user.language_code == "ar" else "en"
    welcome = "🚀 تم تفعيل البوت بنظام الردود السريعة!" if lang == "ar" else "🚀 Bot activated with Fast Response system!"
    bot.reply_to(message, welcome)

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "🛠️ أهلاً بك يا مطوري في لوحة التحكم (نظام الردود العادية).")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    # 1. نظام الحماية (الأمان أولاً)
    if any(word in message.text.lower() for word in BANNED_WORDS):
        bot.delete_message(message.chat.id, message.message_id)
        return

    # 2. تحديد لغة المستخدم تلقائياً
    user_lang = "ar" if message.from_user.language_code == "ar" else "en"
    text = message.text.lower().strip()

    # 3. نظام الردود العادية
    found_response = False
    for key, value in RESPONSES[user_lang].items():
        if key in text:
            bot.reply_to(message, value)
            found_response = True
            break
    
    # 4. رد افتراضي إذا لم يفهم الكلمة
    if not found_response:
        default_msg = "عذراً، لم أفهم هذه الكلمة. جرب قول 'مرحبا' أو 'اوامر'." if user_lang == "ar" else "Sorry, I didn't understand. Try saying 'hello' or 'commands'."
        bot.reply_to(message, default_msg)

# تشغيل النظام
bot.polling(none_stop=True)
