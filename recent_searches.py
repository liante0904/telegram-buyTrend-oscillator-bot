import os
import json
from datetime import datetime
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
    
    # 매번 JSON 파일을 로드하여 최신 상태 유지
    recent_searches_data = load_recent_searches()
    recent_searches = recent_searches_data.get(str(user_id), [])

    # timestamp 키가 없는 경우를 대비해 예외 처리
    recent_searches.sort(key=lambda x: x.get('timestamp', '9999-12-31T23:59:59'), reverse=False)

    if recent_searches:
        message = "최근 검색한 종목들:\n" + "\n".join(search['name'] for search in recent_searches)
    else:
        message = "최근 검색한 종목이 없습니다."
    
    await context.bot.send_message(chat_id=chat_id, text=message)
