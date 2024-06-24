import requests

def search_stock(query):
    url = 'https://ac.stock.naver.com/ac'
    params = {
        'q': query,
        'target': 'index,stock,marketindicator'
    }

    response = requests.get(url, params=params)
    data = response.json()
    print(data)
    # 필터링된 결과를 저장할 리스트
    filtered_items = [
        {
            'name': item['name'],
            'code': item['code']
        }
        for item in data['items']
        if  item['typeCode'] in ['KOSPI', 'KOSDAQ']
        and not (40000 <= int(item['code'][0:5]) <= 49999 and '스팩' in item['name'])
    ]
    print(filtered_items)
    return filtered_items
