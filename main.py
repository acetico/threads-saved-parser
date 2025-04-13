from fastapi import FastAPI, Query, HTTPException
from scrapfly import ScrapflyClient, ScrapeConfig
from threads_utils import parse_thread
from parsel import Selector
import os
import re
import chardet

app = FastAPI()

SCRAPFLY = ScrapflyClient(key=os.environ["SCRAPFLY_KEY"])

@app.get("/")
def root():
    return {"message": "Threads Scraper is working"}

@app.get("/thread")
def thread_api(url: str = Query(...)):
    config = ScrapeConfig(
        url=url,
        asp=True,
        country="US",
        render_js=True
    )
    result = SCRAPFLY.scrape(config)

    # 1. Пробуем JSON
    content_json = result.result.get("content_json")
    if content_json:
        return parse_thread(content_json)

    # 2. Fallback: HTML
    raw_html = result.result.get("content", b"")
    if isinstance(raw_html, bytes):
        # Попробуем угадать кодировку
        detected = chardet.detect(raw_html)
        html = raw_html.decode(detected["encoding"] or "utf-8", errors="ignore")
    else:
        html = raw_html  # уже строка

    selector = Selector(text=html)

    text = selector.css('meta[property="og:description"]::attr(content)').get()
    author = selector.css('meta[property="og:title"]::attr(content)').get()
    image = selector.css('meta[property="og:image"]::attr(content)').get()
    url = selector.css('meta[property="og:url"]::attr(content)').get()
    timestamp_match = re.search(r'"publish_date":"([^"]+)"', html)
    timestamp = timestamp_match.group(1) if timestamp_match else None

    return {
        "text": text or "No text found",
        "author": author or "Unknown",
        "image": image,
        "url": url,
        "published": timestamp
    }
