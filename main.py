import os
import requests
from google import genai
from datetime import datetime, timezone, timedelta

TELEGRAM_TOKEN      = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID             = os.environ.get("CHAT_ID", "")
NAVER_CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

KEYWORDS = ["민자사업", "민자", "butx"]

KST = timezone(timedelta(hours=9))

def now_kst():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M")

def is_today(pub_date):
    try:
        dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
        diff = datetime.now(KST) - dt.astimezone(KST)
        return diff.total_seconds() <= 86400  # 86400초 = 24시간
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


def filter_by_ai(keyword, items):
    if not items:
        return []

    client = genai.Client(api_key=GEMINI_API_KEY)

    articles = ""
    for i, item in enumerate(items):
        title = clean(item["title"])
        desc = clean(item["description"])
        articles += str(i) + ". " + title + " - " + desc + "\n"

    prompt = (
        "아래는 '" + keyword + "' 키워드로 검색된 뉴스 목록입니다.\n"
        "각 기사가 SOC 도로, 철도 민간투자사업과 직접적으로 관련있는지 판단해서 "
        "관련있는 기사 번호만 쉼표로 구분해서 답해주세요. "
        "예시: 0,2,4\n"
        "관련 없으면 '없음'이라고만 답하세요.\n\n"
        + articles
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        answer = response.text.strip()
        print("Gemini 응답 [" + keyword + "]: " + answer)

        if answer == "없음":
            return []

        indices = [int(x.strip()) for x in answer.split(",") if x.strip().isdigit()]
        print("필터링 결과: " + str(len(indices)) + "건 통과")
        return [items[i] for i in indices if i < len(items)]

    except Exception as e:
        print("Gemini 오류: " + str(e))
        return items
        
def build_message():
    lines = ["📰 오늘의 뉴스 브리핑", "🕖 " + now_kst() + " KST", ""]
    total = 0
    seen = set()

    for keyword in KEYWORDS:
        items = search_news(keyword)

        # 오늘 기사 + 중복 제거
        filtered = []
        for item in items:
            link = item.get("originallink") or item.get("link")
            if not is_today(item.get("pubDate", "")):
                continue
            if link in seen:
                continue
            seen.add(link)
            filtered.append(item)

        # AI 필터링 추가
        filtered = filter_by_ai(keyword, filtered)

        if not filtered:
            continue

        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append("🔑 키워드: " + keyword)
        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append("")

        for i, item in enumerate(filtered, 1):
            title = clean(item["title"])
            desc = clean(item["description"])
            link = item.get("originallink") or item["link"]
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
