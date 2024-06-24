# recent_searches.py
import os
import json
from telegram import Update
from telegram.ext import CallbackContext

# 파일 경로 설정
RECENT_SEARCHES_FILE = 'recent_searches.json'

def load_recent_searches():
    if os.path.exists(RECENT_SEARCHES_FILE):
        with open(RECENT_SEARCHES_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def save_recent_searches(recent_searches):
    with open(RECENT_SEARCHES_FILE, 'w', encoding='utf-8') as file:
        json.dump(recent_searches, file, ensure_ascii=False, indent=4)

async def show_recent_searches(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)
    recent_searches = context.bot_data.get('recent_searches', {}).get(user_id, [])
    if recent_searches:
        message = "최근 검색한 종목들:\n" + "\n".join(search['name'] for search in recent_searches)
    else:
        message = "최근 검색한 종목이 없습니다."
    await context.bot.send_message(chat_id=chat_id, text=message)
