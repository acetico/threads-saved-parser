from threads_utils import get_threads
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Threads Scraper is working"}

@app.get("/thread")
def thread_api(url: str = Query(...)):
    return get_thread(url)
