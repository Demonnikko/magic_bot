<details>
<summary>Код для bot/main.py (тапаешь – разворачивается)</summary>
import os, json, sqlite3, asyncio, datetime as dt
from aiogram import Bot, Dispatcher, types, F
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from fastapi import FastAPI, Request
from aiohttp import web

TOKEN   = os.getenv("TOKEN")        # зададим на Render
WEB_URL = os.getenv("WEB")          # https://<логин>.github.io/magic_bot/web
DB      = sqlite3.connect("data.db", check_same_thread=False)
DB.execute("""CREATE TABLE IF NOT EXISTS events(
  user INTEGER, id TEXT PRIMARY KEY, data TEXT)""")

bot = Bot(TOKEN, parse_mode="HTML")
dp  = Dispatcher()

@dp.message(F.text == "/calendar")
async def open_calendar(m: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(
            text="📅 Открыть календарь",
            web_app=types.WebAppInfo(
                url=f"{WEB_URL}/calendar/?u={m.from_user.id}")
        )
    ]])
    await m.reply("Ваш календарь:", reply_markup=kb)

# ---------- FastAPI ----------
api = FastAPI()

@api.post("/api/save")
async def save(req: Request):
    ev = await req.json()
    DB.execute("REPLACE INTO events VALUES(?,?,?)",
               (ev["user"], ev["id"], json.dumps(ev)))
    DB.commit()
    return {"ok": 1}

@api.get("/api/load")
async def load(user: int):
    cur = DB.execute("SELECT data FROM events WHERE user=?", (user,))
    return [json.loads(r[0]) for r in cur]

@api.get("/api/stats")
async def stats(user: int):
    g=p=0
    for fee,pre in DB.execute(
      "SELECT json_extract(data,'$.extendedProps.fee'),"
      "json_extract(data,'$.extendedProps.pre') FROM events WHERE user=?", (user,)):
        g+=(fee or 0); p+=(pre or 0)
    return {"gross":g,"prepay":p,"net":g-p}

# ---------- webhook сервер ----------
async def on_startup(app: web.Application):
    await bot.set_webhook(os.getenv("WEBHOOK_URL"))

app = web.Application()
app.on_startup.append(on_startup)
SimpleRequestHandler(dp, bot).register(app, path="/webhook")
setup_application(app, api, path="/api")
</details>
