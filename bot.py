import os
import telebot
import requests # سنستخدم requests للاتصال المباشر لضمان تجاوز القيود

TOKEN = os.getenv("BOT_TOKEN")
AI_KEY = os.getenv("AI_API_KEY")
ADMIN_ID = 8336468616

bot = telebot.TeleBot(TOKEN)

def get_ai_response(text):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-tiny", # سريع جداً ومناسب للسيرفرات الأوروبية
        "messages": [{"role": "user", "content": text}]
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return "📡 النظام الأوروبي يواجه ضغطاً، حاول مرة أخرى."

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    # نظام الأمان والتحكم
    if any(word in message.text.lower() for word in ["مسيء1", "مسيء2"]):
        bot.delete_message(message.chat.id, message.message_id)
        return

    bot.send_chat_action(message.chat.id, 'typing')
    answer = get_ai_response(message.text)
    bot.reply_to(message, answer)

bot.polling(none_stop=True)
