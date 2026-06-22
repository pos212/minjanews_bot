import os
import sys
import requests
from datetime import datetime, timezone, timedelta

# ── 환경변수 ──────────────────────────────
TELEGRAM_TOKEN      = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID             = os.environ.get("CHAT_ID", "")
NAVER_CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

# ── 키워드 목록 (원하는 것으로 수정) ──────
KEYWORDS = ["민자사업", "민자", "butx"]

KST = timezone(timedelta(hours=9))

def now_kst():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M")

# ── 네이버 뉴스 검색 ──────────────────────
def search_news(keyword: str, display: int = 3) -> list:
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": keyword,
        "display": display,
        "sort": "date",        # 최신순
    }
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    return res.json().get("items", [])

# ── HTML 태그 제거 ────────────────────────
def clean(text: str) -> str:
    return text.replace("<b>", "").replace("</b>", "") \
               .replace("&quot;", '"').replace("&amp;", "&") \
               .replace("&lt;", "<").replace("&gt;", ">")

# ── 메시지 조립 ───────────────────────────
def build_message() -> str:
    lines = [f"📰 *오늘의 뉴스 브리핑*\n🕖 {now_kst()} KST\n"]

    total = 0
    for keyword in KEYWORDS:
        items = search_news(keyword)
        if not items:
            continue

        lines.append(f"━━━━━━━━━━━━━━━━━━")
        lines.append(f"🔑 키워드: `{keyword}`")
        lines.append(f"━━━━━━━━━━━━━━━━━━\n")

        for i, item in enumerate(items, 1):
            title = clean(item["title"])
            desc  = clean(item["description"])
            link  = item["originallink"] or item["link"]
            lines.append(f"*{i}. {title}*")
            lines.append(f"{desc}")
            lines.append(f"🔗 [기사 보기]({link})\n")
            total += 1

    lines.append(f"━━━━━━━━━━━━━━━━━━")
    lines.append(f"📊 오늘 수집: 총 *{total}건*")
    return "\n".join(lines)

# ── 텔레그램 전송 ─────────────────────────
def send_message(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    res = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }, timeout=10)
    res.raise_for_status()
    print("✅ 전송 완료")

# ── 실행 ──────────────────────────────────
if __name__ == "__main__":
    print(f"▶ 시작: {now_kst()} KST")
    message = build_message()
    send_message(message)
    print("▶ 완료")
