from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import os
import json
import asyncio
import re
from package.SecretKey import SecretKey
from stock_search import search_stock
from chart import draw_chart
from recent_searches import load_recent_searches, save_recent_searches, show_recent_searches
from report_search import search_report
from chart_handler import generate_and_send_charts

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text='안녕하세요! 주식 차트 생성 봇입니다. \n 차트를 생성할 주식의 종목명을 입력하세요. \n (종목리스트를 전송하면 다중 전송됩니다. (한줄에 한종목 혹은 쉼표로 구분))')
    context.user_data['next_command'] = 'generate_chart'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    next_command = context.user_data.get('next_command')

    if next_command == 'generate_chart':
        user_input = update.message.text
        # 쉼표와 줄바꿈을 기준으로 입력을 분리
        stock_list = [stock.strip() for stock in re.split('[,\n]', user_input) if stock.strip()]

        context.user_data['stock_list'] = stock_list
        context.user_data['generated_charts'] = []
        await process_stock_list(update, context, user_id, update.message)

async def process_stock_list(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str, message) -> None:
    stock_list = context.user_data.get('stock_list', [])
    remaining_stocks = []

    for stock_name in stock_list:
        results = search_stock(stock_name)
        if results and len(results) == 1:
            stock_name, stock_code = results[0]['name'], results[0]['code']
            await message.reply_text(f"{stock_name}에 대한 차트를 생성 중...")

            # 최근 검색 종목에 추가 (중복 방지)
            if user_id not in context.bot_data['recent_searches']:
                context.bot_data['recent_searches'][user_id] = []
            if not any(search['name'] == stock_name for search in context.bot_data['recent_searches'][user_id]):
                context.bot_data['recent_searches'][user_id].append({'name': stock_name, 'code': stock_code})
            save_recent_searches(context.bot_data['recent_searches'])

            chart_filename = draw_chart(stock_code, stock_name)
            if os.path.exists(chart_filename):
                context.user_data['generated_charts'].append(chart_filename)
            else:
                await message.reply_text(f"차트 파일을 찾을 수 없습니다: {chart_filename}")

        elif results and len(results) > 1:
            buttons = [[InlineKeyboardButton(f"{result['name']} ({result['code']})", callback_data=result['code'])] for result in results]
            reply_markup = InlineKeyboardMarkup(buttons)
            await message.reply_text("검색 결과를 선택하세요:", reply_markup=reply_markup)
            context.user_data['search_results'] = results
            context.user_data['remaining_stocks'] = stock_list[stock_list.index(stock_name) + 1:]
            return
        else:
            await message.reply_text(f"{stock_name} 검색 결과가 없습니다. 다시 시도하세요.")

    # 미디어 그룹을 한 번만 전송
    await generate_and_send_charts_from_files(context, update.effective_chat.id, context.user_data['generated_charts'])

    # 모든 차트 생성 후 상태 재설정
    context.user_data['next_command'] = None
    await context.bot.send_message(chat_id=update.effective_chat.id, text='모든 차트를 전송했습니다. 다른 종목을 검색하시려면 종목명을 입력해주세요.')

async def generate_and_send_charts_from_files(context, chat_id, chart_files):
    media_groups = []
    current_group = []
    files_to_close = []

    for chart_filename in chart_files:
        file = open(chart_filename, 'rb')
        files_to_close.append(file)
        if len(current_group) < 10:
            current_group.append(InputMediaPhoto(file, filename=chart_filename))
        else:
            media_groups.append(current_group)
            current_group = [InputMediaPhoto(file, filename=chart_filename)]

    if current_group:
        media_groups.append(current_group)

    for group in media_groups:
        await context.bot.send_media_group(chat_id=chat_id, media=group)

    for file in files_to_close:
        file.close()

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
            if os.path.exists(chart_filename):
                if 'generated_charts' not in context.user_data:
                    context.user_data['generated_charts'] = []
                context.user_data['generated_charts'].append(chart_filename)
            else:
                await query.edit_message_text(f"차트 파일을 찾을 수 없습니다: {chart_filename}")

    # 나머지 종목 처리
    remaining_stocks = context.user_data.get('remaining_stocks', [])
    if remaining_stocks:
        context.user_data['stock_list'] = remaining_stocks
        await process_stock_list(update, context, user_id, query.message)
    else:
        # 미디어 그룹을 한 번만 전송
        await generate_and_send_charts_from_files(context, update.callback_query.message.chat_id, context.user_data.get('generated_charts', []))
        context.user_data['next_command'] = None
        await context.bot.send_message(chat_id=update.callback_query.message.chat_id, text='모든 차트를 전송했습니다. 다른 종목을 검색하시려면 종목명을 입력해주세요.')

async def set_commands(bot):
    commands = [
        BotCommand("chart", "수급오실레이터 차트"),
        BotCommand("recent", "최근 검색 종목"),
        BotCommand("report", "레포트 검색기")
    ]
    await bot.set_my_commands(commands)

def main():
    secret_key = SecretKey()
    secret_key.load_secrets()
    
    token = secret_key.TELEGRAM_BOT_TOKEN_REPORT_ALARM_SECRET
    application = ApplicationBuilder().token(token).build()

    recent_searches = load_recent_searches()
    application.bot_data['recent_searches'] = recent_searches

    application.add_handler(CommandHandler("chart", chart))  # /chart 명령어 추가
    application.add_handler(CommandHandler("recent", show_recent_searches))  # 최근 검색 종목 명령어 추가
    application.add_handler(CommandHandler("report", search_report))  # 레포트 검색기 명령어 추가
    application.add_handler(CallbackQueryHandler(select_stock, pattern=r'^\d{6}$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # asyncio 이벤트 루프에서 명령어 설정
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_commands(application.bot))

    application.run_polling()

if __name__ == '__main__':
    main()
