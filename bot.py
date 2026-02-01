import os
import telebot
import google.generativeai as genai
from telebot import types

# --- 1. التشخيص وجلب البيانات (DIAGNOSTIC LAYER) ---
# جلب التوكن والمفتاح مع التأكد من حذف أي مسافات زائدة
TOKEN = os.getenv("BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# طباعة تقرير في سجلات Koyeb (للمطور فقط)
print(f"--- System Check ---")
print(f"Bot Token Status: {'Found' if TOKEN else 'NOT FOUND'}")
print(f"Gemini Key Status: {'Found' if GEMINI_API_KEY else 'NOT FOUND'}")

# --- 2. إعداد المحركات (ENGINE SETUP) ---
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 8336468616 

# تفعيل الذكاء الاصطناعي فقط إذا وجد المفتاح
ai_ready = False
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        ai_ready = True
        print("✅ Gemini AI Core: ACTIVATED")
    except Exception as e:
        print(f"❌ Gemini Activation Error: {e}")

# --- 3. قائمة الحظر ولوحة التحكم ---
BANNED_WORDS = ["كلمة1", "مسيء"]

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = "🚀 **تم تفعيل العقل الاصطناعي بنجاح!**" if ai_ready else "⚠️ **البوت يعمل، لكن محرك الذكاء لا يزال غير متصل.**"
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "🛠️ أهلاً بك يا مطوري في لوحة التحكم المركزية.")

# --- 4. معالج الرسائل الذكي (THE BRAIN) ---
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    # فلتر الكلمات
    if any(word in message.text.lower() for word in BANNED_WORDS):
        bot.delete_message(message.chat.id, message.message_id)
        return

    # التفاعل الذكي
    if ai_ready:
        try:
            # إرسال إشارة "جاري الكتابة" لإضفاء واقعية
            bot.send_chat_action(message.chat.id, 'typing')
            response = model.generate_content(message.text)
            bot.reply_to(message, response.text, parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, "📡 عذراً، حدث اضطراب في الاتصال بالمحرك الذكي.")
    else:
        bot.reply_to(message, "❌ المحرك الذكي غير مفعل. تأكد من إضافة GEMINI_API_KEY في Koyeb.")

# تشغيل البوت
bot.polling(none_stop=True)
