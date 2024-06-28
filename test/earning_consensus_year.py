import requests
from bs4 import BeautifulSoup
import pandas as pd

# 종목코드 설정 (예: 삼성전자)
ticker = '005930'

# URL 설정
url = f'http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A{ticker}'

# 데이터 가져오기
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# 영업이익 추정치 테이블 찾기
table = soup.find('div', {'id': 'highlight_D_Y'})

# 테이블 데이터 파싱
data = []
headers = []

# 헤더 추출
for th in table.find_all('th'):
    headers.append(th.get_text().strip())

# 데이터 추출
for row in table.find_all('tr'):
    columns = row.find_all('td')
    if columns:
        data.append([column.get_text().strip() for column in columns])

# 데이터프레임으로 변환
if data:  # 데이터가 있을 때만 데이터프레임 생성
    df = pd.DataFrame(data, columns=headers[2:2+len(data[0])])  # 데이터 길이에 맞게 헤더 길이 조정
    df.insert(0, '항목', ['매출액', '영업이익', '영업이익(발표기준)', '당기순이익', '지배주주순이익', '비지배주주순이익', '자산총계', '부채총계', '자본총계', '지배주주지분', '비지배주주지분', '자본금', '부채비율(%)', '유보율(%)', '영업이익률(%)', '지배주주순이익률(%)', 'ROA(%)', 'ROE(%)', 'EPS(원)', 'BPS(원)', 'DPS(원)', 'PER(배)', 'PBR(배)', '발행주식수', '배당수익률(%)'])
    
    # 영업이익 행 추출
    operating_income = df[df['항목'].str.contains('영업이익', na=False)]

    # 데이터 출력
    print(operating_income.to_markdown(index=False))
else:
    print("No data found")
