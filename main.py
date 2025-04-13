from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from scrapfly import ScrapflyClient, ScrapeConfig
from parsel import Selector
import os
import re
import chardet

app = FastAPI()
SCRAPFLY = ScrapflyClient(key=os.environ["SCRAPFLY_KEY"])

def fetch_html(url: str) -> str:
    config = ScrapeConfig(
        url=url,
        asp=True,
        country="US",
        render_js=True
    )
    result = SCRAPFLY.scrape(config)
    raw_html = result.result.get("content", b"")
    if isinstance(raw_html, bytes):
        detected = chardet.detect(raw_html)
        return raw_html.decode(detected["encoding"] or "utf-8", errors="ignore")
    return raw_html

def extract_posts_from_thread(main_url: str):
    visited_urls = set()
    collected_posts = []

    # 1. Загрузка главной страницы
    main_html = fetch_html(main_url)
    main_sel = Selector(text=main_html)

    # 2. Получаем имя автора
    canonical_url = main_sel.css('link[rel="canonical"]::attr(href)').get()
    match = re.search(r'threads.net/@([^/]+)/post', canonical_url or main_url)
    if not match:
        raise HTTPException(status_code=500, detail="Unable to extract username")
    base_username = match.group(1)
    author = f"@{base_username}"

    def extract_text_and_media(sel: Selector):
        text = sel.css('meta[property="og:description"]::attr(content)').get()
        image = sel.css('meta[property="og:image"]::attr(content)').get()
        return {
            "text": text or "",
            "media": [image] if image else []
        }

    # 3. Собираем первый пост
    first = extract_text_and_media(main_sel)
    collected_posts.append(first)
    visited_urls.add(main_url)

    # 4. Находим все ссылки на продолжения
    post_links = main_sel.css(f'a[href*="/@{base_username}/post/"]::attr(href)').getall()
    post_links = [f"https://www.threads.net{link}" for link in post_links]
    post_links = list(set(post_links) - visited_urls)

    # 5. Загружаем остальные посты автора
    for link in post_links:
        visited_urls.add(link)
        try:
            html = fetch_html(link)
            sel = Selector(text=html)
            this_author = sel.css('meta[property="og:title"]::attr(content)').get()
            if this_author != author:
                continue  # Пропускаем чужие комментарии
            post = extract_text_and_media(sel)
            collected_posts.append(post)
        except Exception as e:
            continue

    # 6. Объединение текста и медиа
    all_texts = [p["text"] for p in collected_posts if p["text"]]
    all_media = sum([p["media"] for p in collected_posts], [])

    return {
        "author": author,
        "posts_count": len(collected_posts),
        "text_full": "\n\n".join(all_texts),
        "media_urls": all_media,
        "source": main_url
    }

@app.get("/thread")
def thread_api(url: str = Query(...)):
    try:
        result = extract_posts_from_thread(url)
        return JSONResponse(content=result, media_type="application/json; charset=utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
