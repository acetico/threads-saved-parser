from fastapi import FastAPI, Query, HTTPException
from scrapfly import ScrapflyClient, ScrapeConfig
from threads_utils import parse_thread
import os

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

    # Пробуем достать JSON
    content_json = result.result.get("content_json")
    if not content_json:
        raise HTTPException(status_code=500, detail="Threads returned HTML instead of JSON. This post may require login or isn't public.")

    return parse_thread(content_json)
