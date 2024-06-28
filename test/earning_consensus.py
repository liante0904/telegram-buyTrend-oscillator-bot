import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# 한글 폰트 설정
font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"  # 시스템에 맞는 경로로 변경 필요
font_manager.fontManager.addfont(font_path)
font_properties = font_manager.FontProperties(fname=font_path)
rc('font', family=font_properties.get_name())

# 종목코드 설정 (예: 삼성전자)
ticker = '005930'

# URL 설정
url = f'http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A{ticker}'

# 데이터 가져오기
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# 분기별 영업이익 추정치 테이블 찾기
table = soup.find('div', {'id': 'highlight_D_Q'})

# 테이블 데이터 파싱
data = []
headers = []

# 헤더 추출
header_row = table.find('thead').find_all('tr')[-1]  # 마지막 tr 태그에서 헤더 정보 추출
for th in header_row.find_all('th'):
    headers.append(th.get_text().strip())

# 데이터 추출
rows = table.find('tbody').find_all('tr')
for row in rows:
    columns = row.find_all('td')
    if columns:
        data.append([column.get_text().strip() for column in columns])

# 헤더와 데이터를 출력
print("Headers:", headers)
print("Data:", data)

# 항목 리스트 (원하는 항목들)
items = [
    '매출액', '영업이익', '영업이익(발표기준)', '당기순이익', '지배주주순이익', '비지배주주순이익', '자산총계', '부채총계', 
    '자본총계', '지배주주지분', '비지배주주지분', '자본금', '부채비율(%)', '유보율(%)', '영업이익률(%)', 
    '지배주주순이익률(%)', 'ROA(%)', 'ROE(%)', 'EPS(원)', 'BPS(원)', 'DPS(원)', 'PER(배)', 'PBR(배)', 
    '발행주식수', '배당수익률(%)'
]

# 데이터프레임으로 변환
if data:  # 데이터가 있을 때만 데이터프레임 생성
    df = pd.DataFrame(data, columns=headers[:len(data[0])])  # 데이터 길이에 맞게 헤더 길이 조정
    df.insert(0, '항목', items[:len(df)])  # 데이터 길이에 맞게 항목 길이 조정

    # 영업이익 행 추출
    operating_income = df[df['항목'].str.contains('영업이익', na=False)]

    # 데이터 출력
    pd.set_option('display.max_columns', None)  # 모든 열이 출력되도록 설정
    print(operating_income)

    # 차트 그리기
    plt.figure(figsize=(10, 6))
    for idx, row in operating_income.iterrows():
        plt.plot(headers, row[1:], marker='o', label=row['항목'])

    plt.title('분기별 영업이익 추정치')
    plt.xlabel('분기')
    plt.ylabel('금액 (억원)')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # 이미지를 파일로 저장
    plt.savefig('operating_income.png')
else:
    print("No data found")
