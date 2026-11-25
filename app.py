import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.sessions import SessionMiddleware
from database import store
from admin_routes import router as admin_router
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from game_engine import GameManager
from telegram_auth import verify_telegram_init_data

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

games = GameManager()

class NewGameRequest(BaseModel):
    pass

class PlayRequest(BaseModel):
    card_id: str
    chosen_color: str | None = None

async def get_user(request: Request) -> dict:
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    if init_data and BOT_TOKEN:
        user = verify_telegram_init_data(init_data, BOT_TOKEN)
        if user:
            return user
    if DEV_MODE:
        return {"id": 10001, "first_name": "تجريبي"}
    raise HTTPException(status_code=401, detail="تعذر التحقق من حساب تيليجرام. افتح اللعبة من البوت.")

app = FastAPI(title="UNO PRO API")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "local-development-secret-change-me"), https_only=os.getenv("COOKIE_SECURE", "false").lower() == "true", same_site="lax")
store.init_db()
app.include_router(admin_router)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def home():
    return FileResponse("static/index.html")

@app.get("/health")
async def health():
    return {"ok": True, "service": "UNO PRO"}

@app.post("/api/game/new")
async def new_game(request: Request):
    user = await get_user(request)
    store.register_user(user["id"], user.get("username", ""), user.get("first_name", ""))
    store.record_game(user["id"])
    state = games.create_game(str(user["id"]), user.get("first_name", "لاعب"))
    return state

@app.get("/api/game")
async def game_state(request: Request):
    user = await get_user(request)
    store.register_user(user["id"], user.get("username", ""), user.get("first_name", ""))
    state = games.get_state(str(user["id"]))
    if not state:
        raise HTTPException(status_code=404, detail="لا توجد مباراة. ابدأ مباراة جديدة.")
    return state

@app.post("/api/game/play")
async def play_card(payload: PlayRequest, request: Request):
    user = await get_user(request)
    store.register_user(user["id"], user.get("username", ""), user.get("first_name", ""))
    try:
        return games.play_card(str(user["id"]), payload.card_id, payload.chosen_color)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/api/game/draw")
async def draw_card(request: Request):
    user = await get_user(request)
    store.register_user(user["id"], user.get("username", ""), user.get("first_name", ""))
    try:
        return games.draw_card(str(user["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
