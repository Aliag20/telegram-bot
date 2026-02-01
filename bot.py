import os
import telebot
from telebot import types

# --- إعدادات الهوية ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8336468616 
bot = telebot.TeleBot(TOKEN)

# --- قاعدة بيانات الردود الضخمة ---
DATA = {
    "ar": {
        "start": "🚀 **أهلاً بك في النسخة المطورة!**\n\nأنا بوت الخدمة السريعة، تم تحديثي لأقصى حد. أرسل أي كلمة لأرد عليك فوراً.",
        "help": "💡 **قائمة المساعدة:**\n- مرحبا: للترحيب\n- من انت: تعريف بالبوت\n- المطور: معلومات المطور\n- الوقت: حالة النظام\n- بنج: قياس السرعة",
        "responses": {
            "مرحبا": "أهلاً بك يا غالي! نورت البوت 😊",
            "من انت": "أنا نظام آلي متطور مصمم لخدمتك بأعلى سرعة ممكنة 🤖",
            "المطور": "تم تطويري بواسطة القائد @Aliag20 (Architect System) 🛠️",
            "الوقت": "النظام يعمل بكفاءة 100% منذ آخر تحديث ⏱️",
            "بنج": "السرعة: 0.001ms (استجابة فورية) ⚡",
            "شكرا": "واجبنا يا بطل! دائماً في الخدمة ❤️"
        }
    },
    "en": {
        "start": "🚀 **Welcome to the Ultra Version!**\n\nI am your high-speed service bot. I've been upgraded to the max.",
        "help": "💡 **Help Menu:**\n- hello: greetings\n- who are you: bot info\n- developer: dev info\n- status: system status\n- ping: speed test",
        "responses": {
            "hello": "Hello there! Welcome to the bot 😊",
            "who are you": "I am an advanced automated system designed to serve you 🤖",
            "developer": "Developed by the Master @Aliag20 🛠️",
            "status": "System is running at 100% efficiency ⏱️",
            "ping": "Speed: 0.001ms (Instant response) ⚡",
            "thanks": "You're very welcome! Always here for you ❤️"
        }
    }
}

# --- لوحة تحكم المطور (Admin Functions) ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("📊 إحصائيات", callback_data="stats")
        btn2 = types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast")
        btn3 = types.InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")
        markup.add(btn1, btn2, btn3)
        bot.reply_to(message, "🛠️ **لوحة تحكم المطور المركزية:**\nمرحباً بك يا سيدي، اختر ما تريد إدارته:", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ نأسف، هذا الأمر مخصص للمطور فقط.")

# --- معالج الرسائل الذكي ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_text = message.text.lower().strip()
    # تحديد اللغة بناءً على النص أو إعدادات المستخدم
    lang = "ar" if any(char in user_text for char in "أبتثجحخدذرزسشصضطظعغفقكلمنهوي") else "en"
    
    if user_text in ["/start", "البداية"]:
        bot.reply_to(message, DATA[lang]["start"], parse_mode="Markdown")
    elif user_text in ["/help", "مساعدة", "اوامر"]:
        bot.reply_to(message, DATA[lang]["help"], parse_mode="Markdown")
    else:
        # البحث في الردود
        response = DATA[lang]["responses"].get(user_text)
        if response:
            bot.reply_to(message, response)
        else:
            # رد ذكي إذا لم توجد الكلمة
            msg = "عذراً، هذه الكلمة غير مسجلة. أرسل 'مساعدة' لرؤية الكلمات المتاحة." if lang == "ar" else "Sorry, keyword not found. Type 'help' to see available words."
            bot.reply_to(message, msg)

# --- معالج الأزرار (Admin Callbacks) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "stats":
        bot.answer_callback_query(call.id, "📊 النظام يعمل بكامل طاقته.")
    elif call.data == "broadcast":
        bot.answer_callback_query(call.id, "📢 قريباً: ميزة الإذاعة لجميع المستخدمين.")

bot.polling(none_stop=True)
