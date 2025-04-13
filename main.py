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

    try:
        json_data = result.result["content_json"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse thread JSON: {e}")

    return parse_thread(json_data)
