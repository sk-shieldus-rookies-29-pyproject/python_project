from pymongo import MongoClient
from datetime import datetime, timedelta
import config  # config.py 임포트

client = MongoClient('mongodb://localhost:27017')
db = client['weather_db']
collection = db['weather_data']

#검증
try:
    client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=3000)
    # 서버에 연결 가능한지 강제 확인
    client.server_info()
    db = client['weather_db']
    collection = db['weather_data']
    print("MongoDB: 연결 성공", 'mongodb://localhost:27017')
except Exception as e:
    print("MongoDB 연결 실패:", e)
    collection = None

def get_cached_data(city):
    # 1시간 내 캐싱된 데이터 찾기
    one_hour_ago = datetime.now() - timedelta(hours=1)
    data = collection.find_one({'city': city, 'timestamp': {'$gt': one_hour_ago}})
    return data

def save_data(city, data):
    # 데이터 저장 (timestamp 추가)
    data['city'] = city
    data['timestamp'] = datetime.now()
    collection.insert_one(data)