from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import auth, chat
from src.core.logging import setup_logging

app = FastAPI()

setup_logging()

app.mount("/static", StaticFiles(directory="src/static"), name="static")


@app.get("/")
async def index():
    return RedirectResponse("static/index.html")


app.include_router(auth.router)
app.include_router(chat.router)
