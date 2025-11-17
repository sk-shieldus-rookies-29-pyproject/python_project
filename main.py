import google_calendar_use
import slack_weather
import python_rss
import github_evens_to_slack
import time
import schedule

def runrun():
    print("=== 통합 작업 시작 ===")

    print("\n>> [Step 1] 📅Google Calendar 작업 실행")
    try:
        google_calendar_use.fetch_calendar_and_send_to_slack()
        print("   -> 캘린더 작업 완료")
    except Exception as e:
        print(f"   [오류] 캘린더 작업 실패: {e}")

    print("\n>> [Step 2] ⛅Weather 작업 실행")
    try:
        slack_weather.main() 
        print("   -> 날씨 작업 완료")
    except Exception as e:
        print(f"   [오류] 날씨 작업 실패: {e}")

    print("\n>> [Step 3] 📜보안 뉴스 rss 작업 실행")
    try:
        python_rss.rss_boannews()
        print("   -> 뉴스 작업 완료")
    except Exception as e:
        print(f"   [오류] 뉴스 작업 실패: {e}")

    print("\n>> [Step 4] 🐙깃허브 작업 실행")
    try:
        github_evens_to_slack.main()
        print("   -> 깃허브 작업 완료")
    except Exception as e:
        print(f"   [오류] 깃허브 작업 실패: {e}")

    print("\n=== 모든 작업이 종료되었습니다 ===")

def main():
    schedule.every().day.at("09:00").do(runrun)
    # 9시 매일 반복 실행 루프
    print("\n\n==============================")
    print(" 09:00마다 전체 작업 실행 시작")
    print("==============================\n")

    while True:
        schedule.run_pending()

        print("\n 09시까지 기다려!...\n")
        time.sleep(60)

if __name__ == "__main__":
    main()