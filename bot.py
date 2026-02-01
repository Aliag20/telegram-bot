import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import random
import string

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode

# ========== إعدادات البوت ==========
BOT_TOKEN = "8336468616:AAGLhhvmNnPv5BB1gZxSJWCXjnsMHAYmMgw"  # ضع توكن البوت هنا
ADMIN_IDS = [8086158965]  # ضع آيدي المطور هنا [123456789, 987654321]
MAIN_ADMIN_ID = None  # ضع آيدي المطور الرئيسي هنا (اختياري)

# تمكين/تعطيل الميزات
ENABLE_WELCOME = True
ENABLE_MODERATION = True
ENABLE_ECONOMY = True
ENABLE_GAMES = True
ENABLE_QUIZ = True
ENABLE_BROADCAST = True
ENABLE_STATS = True
ENABLE_BACKUP = True

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== هياكل البيانات ==========
class Database:
    def __init__(self):
        self.data = {
            "users": {},
            "groups": {},
            "economy": {},
            "settings": {},
            "stats": {}
        }
        self.load_data()
    
    def load_data(self):
        try:
            with open("bot_data.json", "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.save_data()
    
    def save_data(self):
        with open("bot_data.json", "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
    
    def backup_data(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backups/bot_data_backup_{timestamp}.json"
        os.makedirs("backups", exist_ok=True)
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
        return backup_file

db = Database()

# ========== أدوات مساعدة ==========
def is_admin(user_id: int) -> bool:
    """التحقق إذا كان المستخدم من المطورين"""
    return user_id in ADMIN_IDS or user_id == MAIN_ADMIN_ID

def is_main_admin(user_id: int) -> bool:
    """التحقق إذا كان المستخدم المطور الرئيسي"""
    return user_id == MAIN_ADMIN_ID

def log_action(action: str, user_id: int, details: str = ""):
    """تسجيل الإجراءات"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{user_id}] {action} {details}"
    logger.info(log_entry)
    
    # حفظ في ملف السجلات
    with open("action_logs.txt", "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

# ========== نظام الترحيب ==========
async def welcome_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ترحيب بالأعضاء الجدد"""
    if not ENABLE_WELCOME:
        return
    
    chat = update.effective_chat
    new_members = update.message.new_chat_members
    
    for member in new_members:
        if member.id == context.bot.id:
            # البوت انضم للمجموعة
            welcome_msg = "شكراً لإضافتي! 🤖\n\n" \
                         "أنا بوت متعدد الميزات مع لوحة تحكم للمطور.\n" \
                         "اكتب /help لرؤية الأوامر المتاحة."
            await update.message.reply_text(welcome_msg)
            
            # إضافة المجموعة لقاعدة البيانات
            chat_id = str(chat.id)
            if chat_id not in db.data["groups"]:
                db.data["groups"][chat_id] = {
                    "title": chat.title,
                    "members": [],
                    "welcome_message": "مرحباً بك {name} في المجموعة! 👋",
                    "rules": "قواعد المجموعة:\n1. احترام الأعضاء\n2. عدم السبام\n3. المحافظة على الهدوء",
                    "admins": []
                }
            db.save_data()
        else:
            # عضو جديد انضم
            user_id = str(member.id)
            user_name = member.first_name
            
            # حفظ بيانات المستخدم
            if user_id not in db.data["users"]:
                db.data["users"][user_id] = {
                    "username": member.username or user_name,
                    "first_name": member.first_name,
                    "last_name": member.last_name or "",
                    "join_date": datetime.now().isoformat(),
                    "warnings": 0
                }
            
            # إرسال رسالة ترحيب
            chat_data = db.data["groups"].get(str(chat.id), {})
            welcome_msg = chat_data.get("welcome_message", "مرحباً بك {name} في المجموعة! 👋")
            welcome_msg = welcome_msg.replace("{name}", user_name)
            
            await update.message.reply_text(welcome_msg)
            
            # إضافة نقاط أولية إذا كان نظام الاقتصاد مفعلاً
            if ENABLE_ECONOMY:
                if user_id not in db.data["economy"]:
                    db.data["economy"][user_id] = {
                        "coins": 1000,
                        "bank": 0,
                        "inventory": [],
                        "daily_streak": 0,
                        "last_daily": None
                    }
            
            db.save_data()
            log_action("USER_JOINED", member.id, f"in chat {chat.id}")

# ========== الأوامر الأساسية ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البدء"""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == "private":
        welcome_text = f"مرحباً {user.first_name}! 👋\n\n" \
                      "أنا بوت متعدد الميزات مع لوحة تحكم متقدمة للمطور.\n\n" \
                      "🔧 *الميزات المتاحة:*\n" \
                      "• نظام إدارة المجموعات\n" \
                      "• نظام اقتصادي\n" \
                      "• ألعاب وتحديات\n" \
                      "• إحصائيات متقدمة\n" \
                      "• لوحة تحكم للمطور\n\n" \
                      "📚 اكتب /help لرؤية جميع الأوامر"
    else:
        welcome_text = f"مرحباً {user.first_name}! 👋\n" \
                      "اكتب /help في الخاص لرؤية أوامر البوت"
    
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة المساعدة"""
    chat = update.effective_chat
    
    if chat.type == "private":
        help_text = "📚 *قائمة أوامر البوت:*\n\n" \
                   "👤 *أوامر عامة:*\n" \
                   "/start - بدء استخدام البوت\n" \
                   "/help - عرض هذه الرسالة\n" \
                   "/profile - عرض الملف الشخصي\n" \
                   "/id - عرض آيدي المستخدم\n\n"
        
        if ENABLE_ECONOMY:
            help_text += "💰 *نظام الاقتصاد:*\n" \
                        "/balance - عرض الرصيد\n" \
                        "/daily - المكافئة اليومية\n" \
                        "/transfer <آيدي> <مبلغ> - تحويل عملات\n" \
                        "/top - قائمة الأغنياء\n\n"
        
        if ENABLE_GAMES:
            help_text += "🎮 *الألعاب:*\n" \
                        "/dice - رمي النرد\n" \
                        "/flip - رمي العملة\n" \
                        "/guess <رقم> - تخمين الرقم\n\n"
        
        if is_admin(update.effective_user.id):
            help_text += "⚙️ *أوامر المطور:*\n" \
                        "/admin - لوحة تحكم المطور\n" \
                        "/stats - إحصائيات البوت\n" \
                        "/broadcast <رسالة> - إذاعة رسالة\n" \
                        "/backup - نسخ احتياطي للبيانات\n"
    else:
        help_text = "📚 *أوامر المجموعة:*\n\n" \
                   "👤 /id - عرض آيدي المستخدم\n" \
                   "👑 /adminlist - قائمة المشرفين\n" \
                   "📊 /groupinfo - معلومات المجموعة\n\n" \
                   "🛡️ *أوامر الإدارة (للمشرفين فقط):*\n" \
                   "/warn <معرف> - تحذير عضو\n" \
                   "/mute <معرف> <زمن> - كتم عضو\n" \
                   "/ban <معرف> - حظر عضو\n" \
                   "/unban <معرف> - فك حظر عضو\n"
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض آيدي المستخدم"""
    user = update.effective_user
    chat = update.effective_chat
    
    text = f"🆔 *المعلومات الشخصية:*\n\n" \
          f"👤 *اسمك:* {user.full_name}\n" \
          f"📝 *آيدي حسابك:* `{user.id}`\n"
    
    if chat.type != "private":
        text += f"💬 *آيدي المجموعة:* `{chat.id}`\n"
    
    if user.username:
        text += f"📱 *اسم المستخدم:* @{user.username}"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ========== النظام الاقتصادي ==========
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض رصيد المستخدم"""
    if not ENABLE_ECONOMY:
        await update.message.reply_text("⚠️ نظام الاقتصاد معطل حالياً.")
        return
    
    user = update.effective_user
    user_id = str(user.id)
    
    if user_id not in db.data["economy"]:
        db.data["economy"][user_id] = {
            "coins": 1000,
            "bank": 0,
            "inventory": [],
            "daily_streak": 0,
            "last_daily": None
        }
        db.save_data()
    
    economy_data = db.data["economy"][user_id]
    
    text = f"💰 *الرصيد الشخصي:*\n\n" \
          f"👤 *المالك:* {user.full_name}\n" \
          f"💵 *النقود:* {economy_data['coins']} 💰\n" \
          f"🏦 *البنك:* {economy_data['bank']} 💰\n" \
          f"📊 *المجموع:* {economy_data['coins'] + economy_data['bank']} 💰\n" \
          f"🔥 *التتابع اليومي:* {economy_data['daily_streak']} أيام"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def daily_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المكافأة اليومية"""
    if not ENABLE_ECONOMY:
        await update.message.reply_text("⚠️ نظام الاقتصاد معطل حالياً.")
        return
    
    user = update.effective_user
    user_id = str(user.id)
    
    if user_id not in db.data["economy"]:
        db.data["economy"][user_id] = {
            "coins": 1000,
            "bank": 0,
            "inventory": [],
            "daily_streak": 0,
            "last_daily": None
        }
    
    economy_data = db.data["economy"][user_id]
    last_daily = economy_data.get("last_daily")
    
    if last_daily:
        last_date = datetime.fromisoformat(last_daily)
        now = datetime.now()
        
        if now.date() <= last_date.date():
            next_daily = last_date + timedelta(days=1)
            time_left = next_daily - now
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60
            
            await update.message.reply_text(
                f"⚠️ لقد حصلت على مكافأتك اليومية بالفعل!\n"
                f"⏳ الجائزة التالية بعد: {hours} ساعة و {minutes} دقيقة",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # التحقق من التتابع
        if now.date() == (last_date + timedelta(days=1)).date():
            economy_data["daily_streak"] += 1
        else:
            economy_data["daily_streak"] = 1
    else:
        economy_data["daily_streak"] = 1
    
    # حساب المكافأة
    base_reward = 100
    streak_bonus = economy_data["daily_streak"] * 20
    total_reward = base_reward + streak_bonus
    
    economy_data["coins"] += total_reward
    economy_data["last_daily"] = datetime.now().isoformat()
    db.save_data()
    
    text = f"🎉 *مبروك! لقد حصلت على مكافأتك اليومية!*\n\n" \
          f"💰 *المكافأة:* {total_reward} عملة\n" \
          f"📊 *التتابع:* {economy_data['daily_streak']} يوم\n" \
          f"💵 *الرصيد الجديد:* {economy_data['coins']} عملة\n\n" \
          f"🔥 *مكافأة التتابع:* +{streak_bonus} عملة"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ========== الألعاب ==========
async def roll_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لعبة النرد"""
    if not ENABLE_GAMES:
        await update.message.reply_text("⚠️ نظام الألعاب معطل حالياً.")
        return
    
    dice_value = random.randint(1, 6)
    user = update.effective_user
    
    text = f"🎲 *نتيجة رمي النرد:*\n\n" \
          f"👤 *اللاعب:* {user.first_name}\n" \
          f"🎯 *الرقم:* {dice_value}\n\n"
    
    if dice_value == 6:
        text += "🎉 *مبروك! حصلت على الرقم 6!*"
        if ENABLE_ECONOMY:
            user_id = str(user.id)
            if user_id in db.data["economy"]:
                db.data["economy"][user_id]["coins"] += 50
                db.save_data()
                text += "\n💰 *مكافأة:* +50 عملة!"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def coin_flip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رمي العملة"""
    if not ENABLE_GAMES:
        await update.message.reply_text("⚠️ نظام الألعاب معطل حالياً.")
        return
    
    result = random.choice(["صورة", "كتابة"])
    user = update.effective_user
    
    text = f"🪙 *نتيجة رمي العملة:*\n\n" \
          f"👤 *اللاعب:* {user.first_name}\n" \
          f"🎯 *النتيجة:* {result}"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ========== لوحة تحكم المطور ==========
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة تحكم المطور"""
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("⛔ ليس لديك صلاحية الوصول لهذا الأمر.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 إحصائيات البوت", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 إرسال إشعار", callback_data="admin_broadcast")],
        [InlineKeyboardButton("💾 نسخ احتياطي", callback_data="admin_backup")],
        [InlineKeyboardButton("🔄 إعادة تشغيل", callback_data="admin_restart")],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings")],
        [InlineKeyboardButton("📋 سجلات البوت", callback_data="admin_logs")],
        [InlineKeyboardButton("🔐 إدارة المطورين", callback_data="admin_manage_admins")],
        [InlineKeyboardButton("❌ إغلاق", callback_data="admin_close")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"⚙️ *لوحة تحكم المطور*\n\n" \
          f"👤 *المستخدم:* {user.full_name}\n" \
          f"🆔 *آيدي:* {user.id}\n" \
          f"👑 *الصلاحية:* {'مطور رئيسي' if is_main_admin(user.id) else 'مطور'}"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج استدعاءات لوحة التحكم"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not is_admin(user.id):
        await query.edit_message_text("⛔ ليس لديك صلاحية الوصول لهذا الأمر.")
        return
    
    data = query.data
    
    if data == "admin_stats":
        await show_bot_stats(query, context)
    elif data == "admin_broadcast":
        await start_broadcast(query, context)
    elif data == "admin_backup":
        await create_backup(query, context)
    elif data == "admin_restart":
        await restart_bot(query, context)
    elif data == "admin_settings":
        await admin_settings(query, context)
    elif data == "admin_logs":
        await show_logs(query, context)
    elif data == "admin_manage_admins":
        await manage_admins(query, context)
    elif data == "admin_close":
        await query.edit_message_text("✅ تم إغلاق لوحة التحكم.")
    elif data.startswith("admin_"):
        await handle_admin_actions(query, context, data)

async def show_bot_stats(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    """عرض إحصائيات البوت"""
    total_users = len(db.data["users"])
    total_groups = len(db.data["groups"])
    
    # إحصائيات الاقتصاد
    total_coins = 0
    if ENABLE_ECONOMY:
        for user_data in db.data["economy"].values():
            total_coins += user_data.get("coins", 0) + user_data.get("bank", 0)
    
    # حساب النشاط
    active_users = sum(1 for user in db.data["users"].values() 
                      if datetime.now() - datetime.fromisoformat(user.get("join_date", datetime.now().isoformat())) < timedelta(days=7))
    
    text = f"📊 *إحصائيات البوت*\n\n" \
          f"👥 *إجمالي المستخدمين:* {total_users}\n" \
          f"👤 *المستخدمين النشطين (أسبوع):* {active_users}\n" \
          f"💬 *المجموعات:* {total_groups}\n"
    
    if ENABLE_ECONOMY:
        text += f"💰 *إجمالي العملات:* {total_coins}\n"
    
    # إضافة أزرار للرجوع
    keyboard = [
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def start_broadcast(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    """بدء إرسال إشعار"""
    context.user_data["broadcast_mode"] = True
    
    text = "📢 *وضع الإذاعة*\n\n" \
          "أرسل الرسالة التي تريد إذاعتها الآن.\n" \
          "❌ لإلغاء الأمر، اكتب /cancel"
    
    keyboard = [
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إذاعة رسالة للمستخدمين"""
    if not context.user_data.get("broadcast_mode"):
        return
    
    user = update.effective_user
    if not is_admin(user.id):
        return
    
    message = update.message.text
    
    # إلغاء وضع الإذاعة
    if message == "/cancel":
        context.user_data["broadcast_mode"] = False
        await update.message.reply_text("✅ تم إلغاء وضع الإذاعة.")
        return
    
    await update.message.reply_text("🔄 جاري إرسال الرسالة...")
    
    # إرسال الرسالة للمستخدمين
    success = 0
    failed = 0
    
    for user_id in db.data["users"].keys():
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=f"📢 *إشعار من المطور:*\n\n{message}",
                parse_mode=ParseMode.MARKDOWN
            )
            success += 1
            await asyncio.sleep(0.1)  # تجنب حظر التحميل الزائد
        except Exception as e:
            failed += 1
            logger.error(f"فشل إرسال إشعار للمستخدم {user_id}: {e}")
    
    # إرسال النتائج
    result_text = f"✅ *تم إرسال الإشعار بنجاح*\n\n" \
                 f"✅ *المرسل لهم:* {success}\n" \
                 f"❌ *الفاشل:* {failed}\n" \
                 f"📊 *الإجمالي:* {success + failed}"
    
    await update.message.reply_text(result_text, parse_mode=ParseMode.MARKDOWN)
    context.user_data["broadcast_mode"] = False

async def create_backup(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    """إنشاء نسخة احتياطية"""
    if not ENABLE_BACKUP:
        await query.answer("⚠️ نظام النسخ الاحتياطي معطل.", show_alert=True)
        return
    
    try:
        backup_file = db.backup_data()
        
        text = f"✅ *تم إنشاء النسخة الاحتياطية بنجاح*\n\n" \
              f"📁 *اسم الملف:* `{backup_file}`\n" \
              f"📊 *عدد المستخدمين:* {len(db.data['users'])}\n" \
              f"💬 *عدد المجموعات:* {len(db.data['groups'])}"
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        # إرسال ملف النسخ الاحتياطي للمطور
        if query.from_user.id in ADMIN_IDS:
            with open(backup_file, "rb") as f:
                await context.bot.send_document(
                    chat_id=query.from_user.id,
                    document=f,
                    caption=f"📁 نسخة احتياطية - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
    
    except Exception as e:
        logger.error(f"فشل إنشاء نسخة احتياطية: {e}")
        await query.answer("❌ فشل إنشاء النسخة الاحتياطية!", show_alert=True)

async def admin_settings(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    """إعدادات البوت"""
    settings_text = "⚙️ *إعدادات البوت*\n\n" \
                   f"✅ *نظام الترحيب:* {'مفعل' if ENABLE_WELCOME else 'معطل'}\n" \
                   f"✅ *نظام الإدارة:* {'مفعل' if ENABLE_MODERATION else 'معطل'}\n" \
                   f"✅ *نظام الاقتصاد:* {'مفعل' if ENABLE_ECONOMY else 'معطل'}\n" \
                   f"✅ *نظام الألعاب:* {'مفعل' if ENABLE_GAMES else 'معطل'}\n" \
                   f"✅ *نظام الإذاعة:* {'مفعل' if ENABLE_BROADCAST else 'معطل'}\n" \
                   f"✅ *نظام النسخ الاحتياطي:* {'مفعل' if ENABLE_BACKUP else 'معطل'}"
    
    keyboard = [
        [
            InlineKeyboardButton("🔧 تفعيل/تعطيل", callback_data="toggle_settings"),
            InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(settings_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def show_logs(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    """عرض سجلات البوت"""
    try:
        with open("action_logs.txt", "r", encoding="utf-8") as f:
            logs = f.readlines()[-50:]  # آخر 50 سطر
        
        if logs:
            logs_text = "📋 *آخر 50 سجل للبوت:*\n\n"
            for log in logs[-10:]:  # عرض آخر 10 سطور فقط
                logs_text += f"`{log.strip()}`\n"
        else:
            logs_text = "📭 لا توجد سجلات حالياً."
        
        keyboard = [
            [InlineKeyboardButton("🗑️ مسح السجلات", callback_data="clear_logs")],
            [InlineKeyboardButton("📥 تحميل السجلات", callback_data="download_logs")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(logs_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    except FileNotFoundError:
        await query.edit_message_text("📭 لا توجد سجلات حالياً.")

async def manage_admins(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    """إدارة المطورين"""
    if not is_main_admin(query.from_user.id):
        await query.answer("⛔ فقط المطور الرئيسي يمكنه إدارة المطورين.", show_alert=True)
        await admin_panel(update, context)
        return
    
    admins_list = "👑 *قائمة المطورين:*\n\n"
    for i, admin_id in enumerate(ADMIN_IDS, 1):
        admin_data = db.data["users"].get(str(admin_id), {})
        admin_name = admin_data.get("username", f"المستخدم {admin_id}")
        admins_list += f"{i}. {admin_name} - `{admin_id}`\n"
    
    if MAIN_ADMIN_ID:
        main_admin_data = db.data["users"].get(str(MAIN_ADMIN_ID), {})
        main_admin_name = main_admin_data.get("username", f"المستخدم {MAIN_ADMIN_ID}")
        admins_list += f"\n👑 *المطور الرئيسي:*\n{main_admin_name} - `{MAIN_ADMIN_ID}`"
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مطور", callback_data="add_admin")],
        [InlineKeyboardButton("➖ إزالة مطور", callback_data="remove_admin")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(admins_list, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# ========== أوامر الإدارة في المجموعات ==========
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تحذير عضو في المجموعة"""
    if not ENABLE_MODERATION:
        return
    
    user = update.effective_user
    chat = update.effective_chat
    
    # التحقق إذا كان المستخدم مشرف
    member = await chat.get_member(user.id)
    if not (member.status in ["administrator", "creator"] or is_admin(user.id)):
        await update.message.reply_text("⛔ يجب أن تكون مشرفاً لاستخدام هذا الأمر.")
        return
    
    if not context.args:
        await update.message.reply_text("📝 الاستخدام: /warn <معرف المستخدم> [السبب]")
        return
    
    target_id = context.args[0].replace("@", "")
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "لا يوجد سبب"
    
    try:
        # حفظ التحذير
        user_id_str = str(target_id)
        if user_id_str not in db.data["users"]:
            db.data["users"][user_id_str] = {"warnings": 0}
        
        db.data["users"][user_id_str]["warnings"] = db.data["users"][user_id_str].get("warnings", 0) + 1
        warnings = db.data["users"][user_id_str]["warnings"]
        db.save_data()
        
        # إرسال رسالة التحذير
        warning_msg = f"⚠️ *تم تحذير المستخدم*\n\n" \
                     f"👤 *المستخدم:* {target_id}\n" \
                     f"📝 *السبب:* {reason}\n" \
                     f"🔢 *عدد التحذيرات:* {warnings}\n" \
                     f"👮 *المشرف:* {user.first_name}"
        
        await update.message.reply_text(warning_msg, parse_mode=ParseMode.MARKDOWN)
        
        # إذا وصل التحذيرات لـ3 يتم حظر المستخدم
        if warnings >= 3:
            try:
                await chat.ban_member(int(target_id))
                await update.message.reply_text(f"🚫 تم حظر المستخدم {target_id} بسبب تجاوز الحد الأقصى للتحذيرات.")
            except Exception as e:
                logger.error(f"فشل حظر المستخدم: {e}")
        
        log_action("USER_WARNED", user.id, f"target: {target_id}, reason: {reason}")
    
    except Exception as e:
        logger.error(f"فشل تحذير المستخدم: {e}")
        await update.message.reply_text("❌ فشل تحذير المستخدم.")

# ========== الدوال الرئيسية ==========
def main():
    """الدالة الرئيسية لتشغيل البوت"""
    print("🚀 بدء تشغيل بوت تيليجرام المتقدم...")
    
    # إنشاء تطبيق البوت
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("id", get_id))
    
    # أوامر الاقتصاد
    if ENABLE_ECONOMY:
        application.add_handler(CommandHandler("balance", balance))
        application.add_handler(CommandHandler("daily", daily_reward))
    
    # أوامر الألعاب
    if ENABLE_GAMES:
        application.add_handler(CommandHandler("dice", roll_dice))
        application.add_handler(CommandHandler("flip", coin_flip))
    
    # أوامر المطور
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    
    # أوامر الإدارة في المجموعات
    if ENABLE_MODERATION:
        application.add_handler(CommandHandler("warn", warn_user))
    
    # معالجة الترحيب بالأعضاء الجدد
    if ENABLE_WELCOME:
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_user))
    
    # معالجة الإذاعة
    if ENABLE_BROADCAST:
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message))
    
    # معالجة الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    print("✅ تم تشغيل البوت بنجاح!")
    print("🤖 البوت يعمل الآن...")
    application.run_polling(allowed_updates=Update.ALL_UPDATES)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء"""
    logger.error(f"حدث خطأ: {context.error}")
    
    # إرسال رسالة خطأ للمطور
    if ADMIN_IDS:
        error_msg = f"⚠️ *حدث خطأ في البوت:*\n\n`{context.error}`"
        try:
            await context.bot.send_message(
                chat_id=ADMIN_IDS[0],
                text=error_msg,
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass

# ========== بدء التشغيل ==========
if __name__ == "__main__":
    # إنشاء المجلدات اللازمة
    os.makedirs("backups", exist_ok=True)
    
    # تشغيل البوت
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 تم إيقاف البوت.")
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")

