import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_research_data(itemName, itemCode, writeFromDate='', writeToDate=''):
    print(f"Fetching research data for: {itemName} ({itemCode})")
    
    url = 'https://finance.naver.com/research/company_list.naver'
    params = {
        'keyword': '',
        'brokerCode': '',
        'writeFromDate': writeFromDate,
        'writeToDate': writeToDate,
        'searchType': 'itemCode',
        'itemName': itemName,
        'itemCode': itemCode,
        'x': 46,
        'y': 18
    }
    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    columns = ['종목명', '제목', '브로커', '파일보기', '작성일', '번호']
    data = []

    table = soup.find('table', class_='type_1')
    
    if table:
        rows = table.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 6:
                continue
            
            item_name = cols[0].text.strip() if cols[0].find('a', class_='stock_item') else ''
            title = cols[1].text.strip() if cols[1].find('a') else ''
            broker = cols[2].text.strip()
            file_view = cols[3].find('a')['href'] if cols[3].find('a') else ''
            write_date = cols[4].text.strip()
            num = cols[5].text.strip()

            data.append([item_name, title, broker, file_view, write_date, num])
    else:
        print("Table not found on the page.")

    df = pd.DataFrame(data, columns=columns)
    
    print(f"Data fetched: {df.shape[0]} rows")
    return df

def search_stock(item_name, item_code):
    df = get_research_data(itemName=item_name, itemCode=item_code)
    results = []
    if not df.empty:
        for _, row in df.iterrows():
            results.append({
                'name': row['종목명'],
                'title': row['제목'],
                'broker': row['브로커'],
                'link': row['파일보기'],
                'date': row['작성일'],
                'num': row['번호'],
                'code': item_code
            })
    print(f"Search results: {len(results)} found")
    return results

if __name__ == "__main__":
    # 시작일, 종료일, 종목명, 종목코드 설정
    fr_dt = ''
    to_dt = ''
    item_name = '삼성전자'
    item_code = '005930'

    # 검색 실행
    results = search_stock(item_name, item_code)
    for result in results:
        print(result)
