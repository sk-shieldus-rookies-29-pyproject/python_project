import datetime
import os
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv


# .env 파일에서 환경변수를 로드합니다.
load_dotenv() 

# Google Calendar API 사용 시 필요한 권한범위를 읽고 설정합니다.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# .env 파일에서 슬랙 웹훅 URL을 가져옵니다.
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')


# 슬랙 메시지 전송 함수
def send_slack(text: str):
    # 웹훅 URL이 설정되었는지 확인 -> 없을 경우 함수를 종료합니다. 
    if not SLACK_WEBHOOK_URL:
        print("SLACK_WEBHOOK_URL이 없습니다. .env 파일을 확인하세요.")
        return

    try:
        # 슬랙 서버로 POST 요청을 전송합니다.
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": text},
            timeout=10
        )

        # 응답 상태 코드를 확인합니다.
        if response.status_code == 200:
            print("Slack 전송 성공")
        else: 
            # 슬랙 전송이 실패한 경우 응답 상태를 확인합니다. 
            print(f"Slack 전송 실패: {response.status_code} {response.text}")
    except Exception as e: 
        #전송 과정에서 발생한 예외를 출력합니다. 
        print(f"Slack 전송 예외: {e}")


# 캘린더를 조회하고 슬랙에 보낼 데이터를 생성
def fetch_calendar_and_send_to_slack():
    creds = None

    # 사용자 정보를 저장하고 있는 token.json 파일이 있는지 확인합니다.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # token.json 파일이 없거나 있어도 유효하지 않은 경우
    if not creds or not creds.valid:
        # 토큰이 만료되었고 리프레시 토큰이 있는 경우 토큰을 갱신합니다.
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else: # 토큰이 없거나 리프레시 토큰이 없는 경우 신규 인증을 진행합니다.
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            # 로컬 서버를 실행하여 구글 계정 로그인 및 권한 허용 등 사용자 인증을 진행합니다.
            creds = flow.run_local_server(port=0)

        # 갱신되거나 새로 생성된 인증정보를 token.json 파일에 저장합니다.
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # 인증 정보를 사용하여 Calendar API v3 서비스 객체를 생성합니다.
        service = build("calendar", "v3", credentials=creds)

        # API 요청을 위한 오늘의 시간 범위를 설정합니다. (로컬 시간 기준)
        now_local = datetime.datetime.now().astimezone() 
        today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end_local = today_start_local + datetime.timedelta(days=1)

        # Google API가 요구하는 포맷에 맞게 시간을 UTC 기준으로 변환합니다.
        time_min = today_start_local.astimezone(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        time_max = today_end_local.astimezone(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        
        print(f"오늘({today_start_local.strftime('%Y-%m-%d')})의 일정을 가져옵니다.")

        # Google Calendar를 호출합니다. 
        events_result = (
            service.events()
            .list(
                calendarId="primary",   # 사용자의 기본 캘린더
                timeMin=time_min,       # 조회 시작 시간 (오늘 00:00 UTC)
                timeMax=time_max,       # 조회 종료 시간 (내일 00:00 UTC)
                maxResults=20,          # 최대 20개 이벤트
                singleEvents=True,      # 반복 일정을 개별 일정으로 가져오기
                orderBy="startTime",    # 시작 시간 순서로 정렬
            ).execute() # API 실행
        )
        events = events_result.get("items", [])

        
        if not events: # 일정이 없는 경우 
            report_text = f"🗓️ 오늘({today_start_local.strftime('%Y-%m-%d')})의 일정\n- 등록된 일정이 없습니다."
        else: # 일정이 있는 경우
            message_lines = [f"🗓️ 오늘({today_start_local.strftime('%Y-%m-%d')})의 일정"]

            # 각 이벤트를 반복문으로 순회하며 메시지 라인을 추가합니다.
            for event in events:
                summary = event.get("summary", "제목 없음") # 일정 제목
                description = event.get("description", "") # 일정 설명

                # 'dateTime' (특정 시간) 또는 'date' (종일) 키를 가져옵니다.
                start_full = event["start"].get("dateTime", event["start"].get("date"))
                end_full = event["end"].get("dateTime", event["end"].get("date"))

                if 'T' in start_full: # 특정 시간대의 일정
                    start_time = datetime.datetime.fromisoformat(start_full).strftime('%H:%M')
                    end_time = datetime.datetime.fromisoformat(end_full).strftime('%H:%M')
                    time_range = f"{start_time} ~ {end_time}"
                else: # 종일 일정
                    time_range = "하루 종일"

                message_lines.append("\n" + ("-" * 20)) 
                message_lines.append(f"🏷️ {summary}") 
                message_lines.append(f"• 시간: {time_range}")
                message_lines.append(f"• 설명: {description or '없음'}")

            # 리스트로 저장된 메시지들을 하나의 문자열로 연결합니다.
            report_text = "\n".join(message_lines)

        print("--- 최종 리포트 ---")
        print(report_text) 
        print("--------------------")
        send_slack(report_text)


    # Google API 호출 시 발생한 오류를 처리합니다.
    except HttpError as error:
        error_message = f"🚨 캘린더 API 오류가 발생했습니다: {error}"
        print(error_message)
        send_slack(error_message) 

# 스크립트가 직접 실행될 때 함수를 호출합니다. 
if __name__ == "__main__":
    fetch_calendar_and_send_to_slack()