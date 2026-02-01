import os
import telebot
from telebot import types

# --- 🛠️ منطقة التحكم (ضع رقمك هنا) ---
# ملاحظة: إذا رفضك البوت، أرسل كلمة 'هويتي' ليعطيك الرقم الصحيح
ADMIN_ID = 8086158965 

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# --- 🧠 قاعدة البيانات المعرفية (توسيع الذكاء) ---
KNOWLEDGE_BASE = {
    "مرحبا": "أهلاً بك يا قائد! كيف يمكنني مساعدتك في مشروعك اليوم؟ ✨",
    "تحليل": "جاري فحص حالة النظام... 🔍\n- السرعة: ممتازة\n- الذاكرة: مستقرة\n- الاتصال: نشط",
    "المطور": "أنت هو المطور الحقيقي لهذا النظام! @Aliag20 🛠️",
    "مساعدة": "يمكنك سؤالي عن: (مرحبا، تحليل، المطور، بنج، هويتي، مسح)",
    "بنج": "⚡ استجابة النظام: 0.0001 ثانية.",
    "هويتي": "رقم تعريفك (ID) هو: ",
    "مسح": "تم تنظيف ذاكرة الجلسة المؤقتة بنجاح 🧹"
}

# --- 🛡️ نظام إدارة المطور ---
@bot.message_handler(commands=['admin'])
def admin_access(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📊 إحصائيات السيرفر", callback_data="s"))
        markup.add(types.InlineKeyboardButton("📢 رسالة جماعية", callback_data="b"))
        bot.reply_to(message, "👑 **أهلاً بك يا سيدي المطور.**\nلديك كامل الصلاحيات الآن:", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, f"❌ الوصول مرفوض.\nرقمك: `{user_id}` ليس مسجلاً كمالك للنظام.", parse_mode="Markdown")

# --- 🗨️ معالج النصوص الذكي ---
@bot.message_handler(func=lambda message: True)
def smart_reply(message):
    text = message.text.lower().strip()
    user_id = message.from_user.id

    # ميزة كشف الهوية للمطور
    if "هويتي" in text:
        bot.reply_to(message, f"🆔 رقم تعريفك هو: `{user_id}`", parse_mode="Markdown")
        return

    # الردود الذكية بناءً على قاعدة البيانات
    found = False
    for key, response in KNOWLEDGE_BASE.items():
        if key in text:
            bot.reply_to(message, response)
            found = True
            break
    
    # إذا لم يجد الرد، يحاول محاكاة "تفكير" بسيط
    if not found:
        if len(text) > 2:
            bot.reply_to(message, "🤔 يبدو أنك تتحدث عن شيء جديد. سأقوم بتعلم هذا المصطلح قريباً!")
        else:
            bot.reply_to(message, "❓ أرسل 'مساعدة' لرؤية ما يمكنني فعله.")

bot.polling(none_stop=True)

