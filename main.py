import os
import requests
from datetime import datetime, timezone, timedelta

TELEGRAM_TOKEN      = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID             = os.environ.get("CHAT_ID", "")
NAVER_CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

KEYWORDS = ["민자사업", "민자", "butx"]

KST = timezone(timedelta(hours=9))

def now_kst():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M")

def is_today(pub_date):
    try:
        dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
        return dt.astimezone(KST).date() == datetime.now(KST).date()
    except Exception:
        return False

def clean(text):
    return text.replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")

def search_news(keyword, display=10):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": keyword, "display": display, "sort": "date"}
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    return res.json().get("items", [])

def build_message():
    lines = ["📰 오늘의 뉴스 브리핑", "🕖 " + now_kst() + " KST", ""]
    total = 0
    seen = set()

    for keyword in KEYWORDS:
        items = search_news(keyword)
        filtered = []
        for item in items:
            link = item.get("originallink") or item.get("link")
            if not is_today(item.get("pubDate", "")):
                continue
            if link in seen:
                continue
            seen.add(link)
            filtered.append(item)

        if not filtered:
            continue

        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append("🔑 키워드: " + keyword)
        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append("")

        for i, item in enumerate(filtered, 1):
            title = clean(item["title"])
            desc  = clean(item["description"])
            link  = item.get("originallink") or item["link"]
            lines.append(str(i) + ". " + title)
            lines.append(desc)
            lines.append("🔗 " + link)
            lines.append("")
            total += 1

    if total == 0:
        lines.append("오늘 해당 키워드의 뉴스가 없습니다.")
    else:
        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append("📊 오늘 수집: 총 " + str(total) + "건")

    return "\n".join(lines)

def send_message(text):
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    res = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }, timeout=10)
    res.raise_for_status()
    print("전송 완료")

if __name__ == "__main__":
    print("시작: " + now_kst() + " KST")
    send_message(build_message())
    print("완료")
