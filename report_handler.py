# report_handler.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from naver_report_search_pc import search_stock_report
from stock_search import search_stock
from recent_searches import save_recent_searches
from datetime import datetime, timedelta

async def process_report_request(update: Update, context: CallbackContext, user_id: str, message) -> None:
    stock_list = context.user_data.get('stock_list', [])
    writeFromDate = context.user_data.get('writeFromDate', (datetime.today() - timedelta(days=14)).strftime('%Y-%m-%d'))
    writeToDate = datetime.today().strftime('%Y-%m-%d')

    for stock_name in stock_list:
        results = search_stock(stock_name)
        if results and len(results) == 1:
            stock_name, stock_code = results[0]['name'], results[0]['code']
            await fetch_and_send_reports(update, context, user_id, message, stock_name, stock_code, writeFromDate, writeToDate)
        elif results and len(results) > 1:
            buttons = [[InlineKeyboardButton(f"{result['name']} ({result['code']})", callback_data=result['code'])] for result in results]
            reply_markup = InlineKeyboardMarkup(buttons)
            await message.reply_text("검색 결과를 선택하세요:", reply_markup=reply_markup)
            context.user_data['search_results'] = results
            context.user_data['remaining_stocks'] = stock_list[stock_list.index(stock_name) + 1:]
            return
        else:
            await message.reply_text(f"{stock_name} 검색 결과가 없습니다. 다시 시도하세요.")
            return  # 검색 실패 시 "이전 검색" 버튼을 표시하지 않도록 종료

    context.user_data['next_command'] = 'search_report'

async def fetch_and_send_reports(update: Update, context: CallbackContext, user_id: str, message, stock_name: str, stock_code: str, writeFromDate: str, writeToDate: str) -> None:
    await message.reply_text(f"{stock_name}({stock_code}) 레포트를 검색 중...")

    # 최근 검색 종목에 추가 (중복 방지)
    if user_id not in context.bot_data['recent_searches']:
        context.bot_data['recent_searches'][user_id] = []
    if not any(search['name'] == stock_name for search in context.bot_data['recent_searches'][user_id]):
        context.bot_data['recent_searches'][user_id].append({'name': stock_name, 'code': stock_code})
    save_recent_searches(context.bot_data['recent_searches'])

    report_results = search_stock_report(stock_name, stock_code, writeFromDate, writeToDate)
    if report_results:
        # 발간일을 기준으로 오름차순 정렬
        report_results.sort(key=lambda x: x['date'])

        report_messages = [
            f"*제목*: *{result['title']}*\n"
            f"증권사: {result['broker']}\n"
            f"발간일: {result['date']}\n"
            f"[링크]({result['link']})"
            for result in report_results
        ]

        # 메시지 나누어서 전송
        header = f"*종목명*: {stock_name} ({stock_code})\n\n"
        for i in range(0, len(report_messages), 5):
            await message.reply_text(header + "\n\n".join(report_messages[i:i+5]), parse_mode='Markdown', disable_web_page_preview=True)
            header = ""

        # 이전 검색 날짜 업데이트
        context.user_data['writeFromDate'] = (datetime.strptime(writeFromDate, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')

        buttons = [[InlineKeyboardButton("이전 검색", callback_data='previous_search')]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text("이전일자(1달전) 혹은 다른 종목을 검색할 수 있습니다.", reply_markup=reply_markup)
    else:
        await message.reply_text(f"{stock_name}({stock_code})에 대한 레포트를 찾을 수 없습니다.")

async def select_stock(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    selected_code = query.data
    results = context.user_data.get('search_results', [])

    for result in results:
        if result['code'] == selected_code:
            stock_name, stock_code = result['name'], result['code']
            await fetch_and_send_reports(update, context, str(query.from_user.id), query.message, stock_name, stock_code, context.user_data['writeFromDate'], datetime.today().strftime('%Y-%m-%d'))

    # 나머지 종목 처리
    remaining_stocks = context.user_data.get('remaining_stocks', [])
    if remaining_stocks:
        context.user_data['stock_list'] = remaining_stocks
        await process_report_request(update, context, str(query.from_user.id), query.message)

async def previous_search(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    await process_report_request(update, context, user_id, query.message)
