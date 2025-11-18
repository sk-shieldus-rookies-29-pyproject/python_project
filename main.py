#pip install schedule
import schedule
import time

import google_calendar_to_slack
import slack_weather
import python_rss
import github_evens_to_slack

def print_message():
    print("=== 통합 작업 시작 ===")

    print("\n>> [Step 1] 📅Google Calendar 작업 실행")
    try:
        # google_calendar_to_slack 모듈의 메인 함수를 호출합니다.
        google_calendar_to_slack.fetch_calendar_and_send_to_slack()
        print("   -> 캘린더 작업 완료")
    except Exception as e:
        print(f"   [오류] 캘린더 작업 실패: {e}")

    print("\n>> [Step 2] ⛅Weather 작업 실행")
    try:
        # slack_weather 모듈의 메인 함수(main)를 호출합니다.
        slack_weather.main() 
        print("   -> 날씨 작업 완료")
    except Exception as e:
        print(f"   [오류] 날씨 작업 실패: {e}")

    print("\n>> [Step 3] 📜보안 뉴스 rss 작업 실행")
    try:
        # python_rss 모듈의 rss_boannews 함수를 호출합니다.
        python_rss.rss_boannews()
        print("   -> 뉴스 작업 완료")
    except Exception as e:
        print(f"   [오류] 뉴스 작업 실패: {e}")

    print("\n>> [Step 4] 🐙깃허브 작업 실행")
    try:
        # github_evens_to_slack 모듈의 메인 함수(main)를 호출합니다.
        github_evens_to_slack.main()
        print("   -> 깃허브 작업 완료")
    except Exception as e:
        print(f"   [오류] 깃허브 작업 실패: {e}")

    print("\n=== 모든 작업이 종료되었습니다 ===")


# 매일 오전 8시 50분에 실행
# 실행 시간 런하실 때 1~2분 후로 바꿔주세요 
schedule.every().day.at("09:24").do(print_message)

while True:
    schedule.run_pending()
    time.sleep(1)
    
