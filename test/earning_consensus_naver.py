import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import os

# 한글 폰트 설정
font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"  # 시스템에 맞는 경로로 변경 필요
if os.path.exists(font_path):
    font_manager.fontManager.addfont(font_path)
    rc('font', family='NanumGothic')

# 네이버 금융 URL 설정 (삼성전자, 분기 탭)
url = 'https://navercomp.wisereport.co.kr/v2/company/cF1002.aspx?cmp_cd=005930&finGubun=MAIN&frq=1'

# 데이터 가져오기
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# 추정실적 컨센서스 분기 탭 테이블 찾기
table = soup.find('table', {'id': 'cTB25'})

# 테이블 확인 및 HTML 구조 출력
if table:
    print("Table found:")
    print(table.prettify())
else:
    print("No table found")

# 테이블 데이터 파싱
data = []
headers = []

if table:
    # 헤더 추출
    header_rows = table.find('thead').find_all('tr')
    for header_row in header_rows:
        for th in header_row.find_all('th'):
            headers.append(th.get_text().strip())

    # 데이터 추출
    rows = table.find('tbody').find_all('tr')
    for row in rows:
        columns = row.find_all('td')
        if columns:
            data.append([column.get_text().strip() for column in columns])

    # 불필요한 헤더 제거
    headers = [header for header in headers if header not in ['금액', 'YoY']]
    # 데이터의 마지막 열 제거
    data = [row[:-1] for row in data]

    # headers와 data 출력
    print(f"Headers: {headers}")
    print(f"Data: {data}")

    # 데이터프레임으로 변환
    try:
        df = pd.DataFrame(data, columns=headers)
    except ValueError as ve:
        print(f"ValueError: {ve}")
        print(f"Headers: {headers}")
        print(f"Data: {data[:5]}")  # 데이터를 일부만 출력하여 확인

    # '재무년월'과 '영업이익(억원, %)' 열만 추출
    try:
        operating_income = df[['재무년월', '영업이익(억원, %)']]

        # 데이터 출력
        pd.set_option('display.max_columns', None)  # 모든 열이 출력되도록 설정
        print(operating_income)

        # 차트 그리기
        plt.figure(figsize=(10, 6))
        plt.plot(operating_income['재무년월'], operating_income['영업이익(억원, %)'], marker='o', label='영업이익')

        plt.title('분기별 영업이익 추정치')
        plt.xlabel('분기')
        plt.ylabel('금액 (억원)')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # 이미지를 파일로 저장
        plt.savefig('operating_income.png')
        plt.show()
    except KeyError as ke:
        print(f"KeyError: {ke}")
        print(f"Available columns: {df.columns.tolist()}")
else:
    print("No table found")
