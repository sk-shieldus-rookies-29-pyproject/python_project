import datetime
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
SLACK_API_TOKEN = os.getenv("SLACK_API_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")

def send_message(channel, text):
    client = WebClient(token=SLACK_API_TOKEN)
    try:
        response = client.chat_postMessage(
            channel=channel,
            text=text
        )
        print(f"슬랙 메시지 전송 성공: {response['ts']}")
    except SlackApiError as e:
        print(f"슬랙 메시지 전송 오류: {e.response['error']}")

def fetch_calendar_and_send_to_slack():
    
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        now_local = datetime.datetime.now().astimezone() 
        today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end_local = today_start_local + datetime.timedelta(days=1)

        time_min = today_start_local.astimezone(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        time_max = today_end_local.astimezone(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        
        print(f"오늘({today_start_local.strftime('%Y-%m-%d')})의 일정을 가져옵니다.")

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,  
                timeMax=time_max,  
                maxResults=20, 
                singleEvents=True,
                orderBy="startTime",
            ).execute()
        )
        events = events_result.get("items", [])

        if not events:
            report_text = f"🗓️ 오늘({today_start_local.strftime('%Y-%m-%d')})의 일정\n- 등록된 일정이 없습니다."
        else:
            message_lines = [f"🗓️ 오늘({today_start_local.strftime('%Y-%m-%d')})의 일정"]

            for event in events:
                summary = event.get("summary", "제목 없음")
                description = event.get("description", "") 
                start_full = event["start"].get("dateTime", event["start"].get("date"))
                end_full = event["end"].get("dateTime", event["end"].get("date"))

                if 'T' in start_full: 
                    start_time = datetime.datetime.fromisoformat(start_full).strftime('%H:%M')
                    end_time = datetime.datetime.fromisoformat(end_full).strftime('%H:%M')
                    time_range = f"{start_time} ~ {end_time}"
                else:
                    time_range = "하루 종일"

                message_lines.append("\n" + ("-" * 20)) 
                message_lines.append(f"🏷️ {summary}") 
                message_lines.append(f"• 시간: {time_range}")
                message_lines.append(f"• 설명: {description or '없음'}")

            report_text = "\n".join(message_lines)

        print("--- 최종 리포트 ---")
        print(report_text) 
        print("--------------------")
        
        send_message(SLACK_CHANNEL, report_text)

    except HttpError as error:
        error_message = f"🚨 캘린더 API 오류가 발생했습니다: {error}"
        print(error_message)
        send_message(SLACK_CHANNEL, error_message) 


if __name__ == "__main__":
    fetch_calendar_and_send_to_slack()