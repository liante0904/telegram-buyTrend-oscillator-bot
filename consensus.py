import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL을 파라미터로 받는 함수
def fetch_data(fr_dt, to_dt, stext):
    url = f"https://comp.fnguide.com/SVO2/ASP/SVD_Report_Summary_Data.asp?fr_dt={fr_dt}&to_dt={to_dt}&stext={stext}&check=all&sortOrd=5&sortAD=D&_=1719498005590"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    else:
        print("Failed to retrieve data")
        return None

# 파라미터 설정
fr_dt = '20240101'
to_dt = '20240627'
stext = '%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90'  # "삼성전자"를 URL 인코딩한 문자열

# 데이터 가져오기
soup = fetch_data(fr_dt, to_dt, stext)

if soup:
    reports = []
    
    # 전체 텍스트를 가져와서 줄 단위로 분리
    body_text = soup.get_text(separator="\n").split("\n")
    
    # 각 라인을 처리하여 필요한 정보를 추출
    lines = [line.strip() for line in body_text if line.strip()]
    
    i = 0
    while i < len(lines):
        try:
            if '삼성전자' in lines[i]:
                title = lines[i]
                details = []
                
                # 날짜 추출
                date_part1 = lines[i-3]
                date_part2 = lines[i-2]
                date_part3 = lines[i-1]
                date_text = f"{date_part1}{date_part2}{date_part3}"

                i += 1
                while i < len(lines) and not (lines[i].startswith('BUY') or lines[i].startswith('매수')):
                    details.append(lines[i])
                    i += 1
                
                rating = lines[i]
                target_price = lines[i + 1]
                current_price = lines[i + 2]
                analyst = lines[i + 3]
                
                report = {
                    'Date': date_text,
                    'Title': title,
                    'Details': details,
                    'Rating': rating,
                    'Target Price': target_price,
                    'Current Price': current_price,
                    'Analyst': analyst
                }
                
                # 중간 결과 출력
                print(report)
                reports.append(report)
                
                i += 4  # 다음 보고서로 이동
            else:
                i += 1  # 보고서 시작이 아니면 다음 라인으로 이동

        except Exception as e:
            print(f"Error processing line: {lines[i]}, error: {e}")
            i += 1  # 오류 발생 시 다음 라인으로 이동

    df = pd.DataFrame(reports)

    # 컬럼명 변경
    df.rename(columns={'Title': '타이틀', 'Target Price': '목표주가', 'Current Price': '현재가격'}, inplace=True)


    # 데이터프레임을 CSV 파일로 저장
    df.to_csv('report_data.csv', index=False, encoding='utf-8-sig')
    
    print(df.head())  # 데이터프레임의 상위 5개 행 출력

else:
    print("No data found")
