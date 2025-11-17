import requests
from datetime import datetime, timedelta
import config  # .env 로드
import models  # MongoDB 캐싱

CITY_COORDS = {'seoul': {'nx': 60, 'ny': 127}}  # 가이드 2. 참고자료 - 단기예보 지점 좌표(X,Y) 참조: 서울 nx=60, ny=127 엑셀 값.

def get_latest_base_time():
    now = datetime.now()
    base_times = ['0200', '0500', '0800', '1100', '1400', '1700', '2000', '2300']  # 가이드 2. 참고자료 - 예보 발표시각 ❍ 단기예보 발표시각 참조: 1일 8회 시간대.
    current_hour = now.hour
    for bt in reversed(base_times):
        bt_hour = int(bt[:2])
        if current_hour >= bt_hour + (1 if int(bt[2:]) > 0 else 0):
            return bt
    return '2300'

def fetch_current_weather(city):
    coords = CITY_COORDS.get(city.lower())
    if not coords:
        return None
    base_date = datetime.now().strftime('%Y%m%d')  # 가이드 1.1 다. 상세기능내역 1) [초단기실황조회] b) 요청 메시지 명세 - base_date 필수 참조: YYYYMMDD 형식.
    base_time = (datetime.now() - timedelta(minutes=10)).strftime('%H00')  # 가이드 2. 참고자료 ❍ 초단기실황 발표시각 참조: 매시 10분 후 업데이트.
    url = 'https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'  # 가이드 1.1 가. API 서비스 개요 - 서비스 URL 참조: VilageFcstInfoService_2.0.
    params = {
        'serviceKey': config.SERVICE_KEY,  # 가이드 1.1 다. 상세기능내역 1) b) 요청 메시지 명세 - serviceKey 필수 참조: URL Encode된 인증키.
        'numOfRows': '100',  # 가이드 1.1 다. 상세기능내역 1) b) numOfRows 참조: 한 페이지 결과 수 (Default:10).
        'dataType': 'JSON',  # 가이드 1.1 다. 상세기능내역 1) b) dataType 참조: JSON/XML (Default:XML).
        'base_date': base_date,
        'base_time': base_time,  # 가이드 1.1 다. 상세기능내역 1) b) base_time 참조: HH00 형식, 매시 10분 후 호출.
        'nx': coords['nx'],  # 가이드 1.1 다. 상세기능내역 1) b) nx 참조: 예보지점 X 좌표 (엑셀 참조).
        'ny': coords['ny']   # 가이드 1.1 다. 상세기능내역 1) b) ny 참조: 예보지점 Y 좌표.
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print('초단기실황 API 실패:', response.text)  # 가이드 2. 참고자료 ※ Open API 에러 코드 정리 참조: 에러 코드(00=정상, 30=키 오류 등) 확인.
        return None
    items = response.json()['response']['body']['items']['item']  # 가이드 1.1 다. 상세기능내역 1) d) 응답 메시지 예제 참조: items 배열.
    current = {'current_temp': None}
    for item in items:
        if item['category'] == 'T1H':  # 가이드 1.1 다. 상세기능내역 1) c) 응답 메시지 명세 - category 참조: T1H=기온 실황 값.
            current['current_temp'] = item['obsrValue']  # 가이드 1.1 다. 상세기능내역 1) c) obsrValue 참조: 실황 값 (실수/정수).
    return current

def fetch_weather(city):
    coords = CITY_COORDS.get(city.lower())
    if not coords:
        return None
    base_date = datetime.now().strftime('%Y%m%d')  # 가이드 1.1 다. 상세기능내역 3) [단기예보조회] b) 요청 메시지 명세 - base_date 필수 참조.
    base_time = get_latest_base_time()  # 가이드 1.1 다. 상세기능내역 3) b) base_time 참조: 0500 등 8회 시간대.
    url = 'https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'  # 가이드 1.1 다. 상세기능내역 3) a) Call Back URL 참조.
    params = {
        'serviceKey': config.SERVICE_KEY,
        'numOfRows': '1000',  # 가이드 1.1 다. 상세기능내역 3) b) numOfRows 참조: 충분히 가져옴 (Default:10).
        'dataType': 'JSON',
        'base_date': base_date,
        'base_time': base_time,
        'nx': coords['nx'],
        'ny': coords['ny']
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print('단기예보 API 실패:', response.text)  # 가이드 2. 참고자료 에러 코드 참조.
        return None
    items = response.json()['response']['body']['items']['item']
    weather_data = {'max_temp': None, 'min_temp': None, 'precip_prob': None, 'precip_amt': None}
    for item in items:
        if item['fcstDate'] == base_date:  # 가이드 1.1 다. 상세기능내역 3) c) fcstDate 참조: 오늘 예보 필터.
            if item['category'] == 'TMX':  # 가이드 1.1 다. 상세기능내역 3) c) category 참조: TMX=최고온도.
                weather_data['max_temp'] = item['fcstValue']  # 가이드 1.1 다. 상세기능내역 3) c) fcstValue 참조: 실수/정수 값.
            elif item['category'] == 'TMN':  # TMN=최저온도.
                weather_data['min_temp'] = item['fcstValue']
            elif item['category'] == 'POP':  # POP=강수확률.
                if weather_data['precip_prob'] is None:
                    weather_data['precip_prob'] = item['fcstValue']
            elif item['category'] == 'PCP':  # PCP=1시간 강수량, 가이드 2. 참고자료 - 강수량(PCP) 범주 참조: mm 단위 표시.
                if weather_data['precip_amt'] is None:
                    weather_data['precip_amt'] = item['fcstValue']
    return weather_data

def send_to_slack(city, data):
    webhook_url = config.SLACK_WEBHOOK_URL
    message = {
        'text': f"{city} 날씨: 현재 {data.get('current_temp', 'N/A')}도, 최고 {data.get('max_temp', 'N/A')}도, 최저 {data.get('min_temp', 'N/A')}도, 강수확률 {data.get('precip_prob', 'N/A')}%, 강수량 {data.get('precip_amt', 'N/A')}"
    }
    response = requests.post(webhook_url, json=message)
    if response.status_code == 200:
        print('Slack 메시지 전송 성공')
    else:
        print('Slack 실패:', response.text)

def main():
    city = 'seoul'
    cached = models.get_cached_data(city)
    if cached:
        send_to_slack(city, cached)
    else:
        current = fetch_current_weather(city) or {'current_temp': 'N/A'}
        weather = fetch_weather(city) or {'max_temp': 'N/A', 'min_temp': 'N/A', 'precip_prob': 'N/A', 'precip_amt': 'N/A'}
        data = {
            'city': city,
            'current_temp': current['current_temp'],
            'max_temp': weather['max_temp'],
            'min_temp': weather['min_temp'],
            'precip_prob': weather['precip_prob'],
            'precip_amt': weather['precip_amt']
        }
        models.save_data(city, data)
        send_to_slack(city, data)

if __name__ == '__main__':
    main()