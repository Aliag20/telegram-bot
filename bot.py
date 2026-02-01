import os
import telebot
from telebot import types
import datetime

# --- الإعدادات الأساسية (SECURITY LAYER) ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8336468616  # تأكد من وضع ID حسابك الصحيح هنا
bot = telebot.TeleBot(TOKEN)

# --- قائمة الكلمات المسيئة (CONTENT SHIELD) ---
BANNED_WORDS = ["كلمة1", "كلمة2", "مسيء"] # أضف الكلمات التي تريد حظرها هنا

# --- بيانات البوت (DATA LAYER) ---
users = set() # لحفظ عدد المستخدمين
bot_status = "Online 🟢"

# --- دوال الحماية ---
def is_admin(user_id):
    return user_id == ADMIN_ID

# --- 1. لوحة تحكم المطور (ADMIN CONTROL PANEL) ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ خطأ في الوصول: أنت لا تملك صلاحيات المطور.")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📊 إحصائيات", callback_data="stats")
    btn2 = types.InlineKeyboardButton("📢 إذاعة للمستخدمين", callback_data="broadcast")
    btn3 = types.InlineKeyboardButton("🔄 إعادة تشغيل النظام", callback_data="restart")
    btn4 = types.InlineKeyboardButton("🛡️ سجل المحظورات", callback_data="banned_logs")
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.send_message(message.chat.id, "🛠️ **لوحة تحكم المطور الرئيسية**\nمرحباً بك في وحدة التحكم المركزية.", parse_mode="Markdown", reply_markup=markup)

# --- 2. معالج الرسائل والذكاء (INTELLIGENCE LAYER) ---
@bot.message_handler(func=lambda message: True)
def filter_and_process(message):
    users.add(message.from_user.id) # إضافة مستخدم جديد للإحصائيات
    
    # فحص الكلمات المسيئة
    for word in BANNED_WORDS:
        if word in message.text.lower():
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, f"⚠️ عزيزي {message.from_user.first_name}، تم حذف رسالتك لمخالفتها قوانين الأمان.")
            return

    # الأوامر الرئيسية
    if message.text == "/start":
        welcome_msg = "⚡ **نظام التفاعل الذكي مفعّل**\n\nأنا بوت متعدد المهام، كيف يمكنني مساعدتك اليوم؟"
        bot.send_message(message.chat.id, welcome_msg, parse_mode="Markdown")
    
    # هنا يتم استدعاء محرك الذكاء الاصطناعي (Gemini / ChatGPT)
    elif not message.text.startswith('/'):
        bot.reply_to(message, "📡 **جاري التحليل...**\nسأقوم بمعالجة طلبك بأعلى دقة قريباً.")

# --- 3. معالجة أزرار التحكم (CALLBACK HANDLER) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "stats":
        bot.answer_callback_query(call.id, "جاري جلب البيانات...")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                              text=f"📊 **إحصائيات النظام:**\n\n👥 عدد المستخدمين: {len(users)}\n🕒 وقت العمل: {datetime.datetime.now().strftime('%Y-%m-%d')}\n✅ الحالة: {bot_status}", parse_mode="Markdown")

# تشغيل المحرك
print("--- [SUCCESS] البوت الذكي يعمل بأمان عالي الآن ---")
bot.polling(none_stop=True)
