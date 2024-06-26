# chart_handler.py
from telegram import InputMediaPhoto
import os
from stock_search import search_stock
from chart import draw_chart, get_last_date, CHART_DIR
from recent_searches import save_recent_searches

async def generate_and_send_charts(context, chat_id, stock_list, user_id):
    media_groups = []
    current_group = []
    files_to_close = []

    for stock_name in stock_list:
        results = search_stock(stock_name)
        if results and len(results) == 1:
            stock_name, stock_code = results[0]['name'], results[0]['code']

            # 차트 파일 생성
            chart_filename = draw_chart(stock_code, stock_name)
            if os.path.exists(chart_filename):
                file = open(chart_filename, 'rb')
                files_to_close.append(file)
                if len(current_group) < 10:
                    current_group.append(InputMediaPhoto(file, filename=chart_filename))
                else:
                    media_groups.append(current_group)
                    current_group = [InputMediaPhoto(file, filename=chart_filename)]

                # 최근 검색 종목에 추가 (중복 방지)
                if user_id not in context.bot_data['recent_searches']:
                    context.bot_data['recent_searches'][user_id] = []
                if not any(search['name'] == stock_name for search in context.bot_data['recent_searches'][user_id]):
                    context.bot_data['recent_searches'][user_id].append({'name': stock_name, 'code': stock_code})
                save_recent_searches(context.bot_data['recent_searches'])
        else:
            continue  # 검색 결과가 없거나 여러 개인 경우 건너뜁니다.

    if current_group:
        media_groups.append(current_group)

    for group in media_groups:
        await context.bot.send_media_group(chat_id=chat_id, media=group)
    
    for file in files_to_close:
        file.close()

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
