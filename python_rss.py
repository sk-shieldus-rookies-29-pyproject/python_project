from flask import Flask, render_template, request
import feedparser
import requests
import config

# 슬랙에 메세지 보내는 함수, 웹흑 url 이용
def send_to_slack(text):
    webhook_url = config.SLACK_WEBHOOK_URL
    payload = { 'text': text }
    requests.post(webhook_url, json=payload)

#보안뉴스 rss 이용해 기사 3개 가져와 출력하기
def rss_boannews():
    # rss url 
    rss_url='http://www.boannews.com/media/news_rss.xml?mkind=1'
    # feed parser로 구문 분석
    feed=feedparser.parse(rss_url)
    #print(feed)

    # number는 기사 개수
    number=1

    # 슬랙에 보낼 메세지 작성
    slack_message = "📢 보안뉴스 주요 내용\n\n"
    for entry in feed.entries:
        # 기사 제목과 링크, 날짜 출력
        print(f'{number}\n{entry.title}\n{entry.link}\n{entry.updated}\n')
        slack_message += f"{number}. {entry.title}\n🔗 {entry.link}\n🕒 {entry.updated}\n\n"
        number+=1
        # 기사는 3개까지 
        if number==4:
            break
    
    #슬랙으로 메세지 전송 
    send_to_slack(slack_message)

if __name__ == '__main__':
    rss_boannews()