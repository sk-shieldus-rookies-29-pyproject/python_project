import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_KEY = os.getenv('SERVICE_KEY')  # 가이드 1.1 가. API 서비스 개요 - serviceKey 필수 파라미터 참조: 공공데이터포털 발급 키 사용.
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')  # Slack Incoming Webhook URL

