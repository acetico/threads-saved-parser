from threads import Threads
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Threads Scraper is working"}

@app.get("/thread")
def get_thread(url: str = Query(...)):
    t = Threads()
    thread = t.get_thread(url)
    return thread