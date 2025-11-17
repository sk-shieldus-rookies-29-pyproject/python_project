from flask import Flask, render_template, request
import feedparser

#보안뉴스 rss 이용해 기사 3개 가져와 출력하기
def rss_boannews():
    # rss url 
    rss_url='http://www.boannews.com/media/news_rss.xml?mkind=1'
    # feed parser로 구문 분석
    feed=feedparser.parse(rss_url)
    #print(feed)

    # number는 기사 개수
    number=1
    for entry in feed.entries:
        # 기사 제목과 링크, 날짜 출력
        print(f'{number}\n{entry.title}\n{entry.link}\n{entry.updated}\n')
        number+=1
        # 기사는 3개까지 
        if number==4:
            break

rss_boannews()