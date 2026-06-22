# 기사 링크를 set으로 관리
seen_links = set()
if link in seen_links:
    continue
seen_links.add(link)
