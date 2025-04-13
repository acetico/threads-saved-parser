from fastapi import FastAPI, Query
from scrapfly import ScrapflyClient, ScrapeConfig
from threads_utils import parse_thread
import os

app = FastAPI()

# Инициализация клиента Scrapfly
SCRAPFLY = ScrapflyClient(key=os.environ["SCRAPFLY_KEY"])

@app.get("/")
def root():
    return {"message": "Threads Scraper is working"}

@app.get("/thread")
def thread_api(url: str = Query(...)):
    # Конфигурация запроса
    config = ScrapeConfig(
        url=url,
        asp=True,
        country="US",
        render_js=True
    )
    result = SCRAPFLY.scrape(config)
    json_data = result.selector.json()
    return parse_thread(json_data)
