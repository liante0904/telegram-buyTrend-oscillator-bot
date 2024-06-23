from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import os
import json
import asyncio
from package.SecretKey import SecretKey
from stock_search import search_stock
from chart import draw_chart

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text='안녕하세요! 주식 차트 생성 봇입니다. 차트를 생성할 주식의 종목명을 입력하세요.')
    context.user_data['next_command'] = 'generate_chart'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    recent_searches = context.bot_data.get('recent_searches', {}).get(user_id, [])
    next_command = context.user_data.get('next_command')

    if next_command == 'generate_chart':
        user_input = update.message.text
        results = search_stock(user_input)

        if results:
            if len(results) == 1:
                stock_name, stock_code = results[0]['name'], results[0]['code']
                await update.message.reply_text(f"{stock_name}에 대한 차트를 생성 중...")

                # 최근 검색 종목에 추가 (중복 방지)
                if user_id not in context.bot_data['recent_searches']:
                    context.bot_data['recent_searches'][user_id] = []
                if not any(search['name'] == stock_name for search in context.bot_data['recent_searches'][user_id]):
                    context.bot_data['recent_searches'][user_id].append({'name': stock_name, 'code': stock_code})
                save_recent_searches(context.bot_data['recent_searches'])

                chart_filename = draw_chart(stock_code, stock_name)
                print(f"Generated chart file: {chart_filename}")
                if os.path.exists(chart_filename):
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(chart_filename, 'rb'))
                else:
                    await update.message.reply_text(f"차트 파일을 찾을 수 없습니다: {chart_filename}")

                # /start 명령을 자동으로 호출하고 상태를 재설정
                context.user_data['next_command'] = None
                await start(update, context)
            else:
                buttons = [[InlineKeyboardButton(f"{result['name']} ({result['code']})", callback_data=result['code'])] for result in results]
                reply_markup = InlineKeyboardMarkup(buttons)
                await update.message.reply_text("검색 결과를 선택하세요:", reply_markup=reply_markup)
                context.user_data['search_results'] = results
        else:
            await update.message.reply_text("검색 결과가 없습니다. 다시 시도하세요.")

async def select_stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    selected_code = query.data
    results = context.user_data.get('search_results', [])

    for result in results:
        if result['code'] == selected_code:
            stock_name, stock_code = result['name'], result['code']
            await query.edit_message_text(f"{stock_name}에 대한 차트를 생성 중...")

            # 최근 검색 종목에 추가 (중복 방지)
            user_id = str(query.from_user.id)
            if user_id not in context.bot_data['recent_searches']:
                context.bot_data['recent_searches'][user_id] = []
            if not any(search['name'] == stock_name for search in context.bot_data['recent_searches'][user_id]):
                context.bot_data['recent_searches'][user_id].append({'name': stock_name, 'code': stock_code})
            save_recent_searches(context.bot_data['recent_searches'])

            chart_filename = draw_chart(stock_code, stock_name)
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(chart_filename, 'rb'))
            break

    # /start 명령을 자동으로 호출하고 상태를 재설정
    context.user_data['next_command'] = None
    await start(update, context)

async def show_recent_searches(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)
    recent_searches = context.bot_data.get('recent_searches', {}).get(user_id, [])
    if recent_searches:
        message = "최근 검색한 종목들:\n" + "\n".join(search['name'] for search in recent_searches)
    else:
        message = "최근 검색한 종목이 없습니다."
    await context.bot.send_message(chat_id=chat_id, text=message)

async def set_commands(bot):
    commands = [
        BotCommand("start", "시작하기"),
        BotCommand("recent", "최근 검색 종목")
    ]
    await bot.set_my_commands(commands)

def main():
    secret_key = SecretKey()
    secret_key.load_secrets()
    
    token = secret_key.TELEGRAM_BOT_TOKEN_MAGIC_FORMULA_SECRET
    application = ApplicationBuilder().token(token).build()

    recent_searches = load_recent_searches()
    application.bot_data['recent_searches'] = recent_searches

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("recent", show_recent_searches))  # 최근 검색 종목 명령어 추가
    application.add_handler(CallbackQueryHandler(select_stock, pattern=r'^\d{6}$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # asyncio 이벤트 루프에서 명령어 설정
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_commands(application.bot))

    application.run_polling()

if __name__ == '__main__':
    main()
