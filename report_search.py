# report_search.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from stock_search import search_stock

async def search_report(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text.split(' ', 1)[1]  # '/report' 명령어 뒤에 오는 텍스트를 가져옴
    results = search_stock(user_input)

    if results:
        if len(results) == 1:
            stock_name, stock_code = results[0]['name'], results[0]['code']
            await update.message.reply_text(f"종목명: {stock_name}\n종목코드: {stock_code}")
        else:
            buttons = [[InlineKeyboardButton(f"{result['name']} ({result['code']})", callback_data=result['code'])] for result in results]
            reply_markup = InlineKeyboardMarkup(buttons)
            await update.message.reply_text("검색 결과를 선택하세요:", reply_markup=reply_markup)
            context.user_data['search_results'] = results
    else:
        await update.message.reply_text("검색 결과가 없습니다. 다시 시도하세요.")
