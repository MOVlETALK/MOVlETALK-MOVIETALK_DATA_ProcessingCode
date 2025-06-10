import requests
import csv
import json
import re

API_KEY = 'your-key'    # your-key에 발급받은 Key를 넣어주세요.
API_URL = 'https://api.koreafilm.or.kr/openapi-data2/wisenut/search_api/search_json2.jsp'

FIELDNAMES = [
    'createDts', 'releaseDts', 'nation', 'genre', 'movieSeq',
    'title', 'director', 'actor', 'plot', 'titleEng', 'runtime', 'rating', 'posterUrl'
]

results = []
list_count = 100
start_count = 1
total_count = None
page_num = 1

# ⛑ 제어문자 제거 함수
def clean_json_text(text):
    return re.sub(r'[\x00-\x1F\x7F]', '', text)

while True:
    params = {
        'collection': 'kmdb_new2',
        'ServiceKey': API_KEY,
        'nation': '대한민국',
        'listCount': list_count,
        'startCount': start_count
    }

    response = requests.get(API_URL, params=params)
    if response.status_code != 200:
        print(f"❌ HTTP 오류 (status {response.status_code})")
        break

    try:
        cleaned_text = clean_json_text(response.text)
        data = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패 (페이지 {page_num}):", e)
        with open(f'error_response_page_{page_num}.json', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"⚠️ 에러 응답이 'error_response_page_{page_num}.json' 파일에 저장됨")
        start_count += list_count
        page_num += 1
        continue

    if total_count is None:
        total_count = int(data.get('TotalCount', 0))
        print(f"🎞 전체 한국 영화 수: {total_count}편")

    batch = []
    for item in data.get('Data', []):
        for movie in item.get('Result', []):
            try:
                batch.append({
                    'createDts': movie.get('prodYear'),
                    'releaseDts': movie.get('repRlsDate'),
                    'nation': movie.get('nation'),
                    'genre': movie.get('genre'),
                    'movieSeq': movie.get('movieSeq'),
                    'title': movie.get('title'),
                    'director': ', '.join([d.get('directorNm') for d in movie.get('directors', {}).get('director', [])]),
                    'actor': ', '.join([a.get('actorNm') for a in movie.get('actors', {}).get('actor', [])]),
                    'plot': movie.get('plots', {}).get('plot', [{}])[0].get('plotText'),
                    'titleEng': movie.get('titleEng'),
                    'runtime': movie.get('runtime'),
                    'rating': movie.get('rating'),
                    'posterUrl': movie.get('posters').split('|')[0] if movie.get('posters') else ''
                })
            except Exception as e:
                print(f"⚠️ 영화 하나 파싱 실패 (movieSeq={movie.get('movieSeq')}): {e}")
                continue

    results.extend(batch)
    print(f"✅ {start_count} ~ {start_count + list_count - 1}까지 수집 완료 ({len(batch)}건)")

    start_count += list_count
    page_num += 1

    if start_count > total_count or len(batch) == 0:
        break

# CSV 저장
with open('kmdb_movies.csv', mode='w', newline='', encoding='cp949', errors='ignore') as file:
    writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print(f"\n📁 CSV 저장 완료: 총 {len(results)}건 → kmdb_movies.csv")