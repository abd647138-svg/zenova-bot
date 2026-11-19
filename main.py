import os, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")
    def log_message(self, *args):
        pass

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# نجيبو الموديلات المتوفرة عندك من جوجل تلقائيا
CACHED_MODEL = None

def get_model():
    global CACHED_MODEL
    if CACHED_MODEL:
        return CACHED_MODEL
    try:
        r = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}", timeout=20)
        data = r.json()
        models = data.get("models", [])
        # نفضل موديل flash
        for m in models:
            name = m.get("name", "")
            methods = m.get("supportedGenerationMethods", [])
            if "generateContent" in methods and "flash" in name:
                CACHED_MODEL = name.replace("models/", "")
                return CACHED_MODEL
        # لو مفيش flash خود اول واحد يدعم generateContent
        for m in models:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                CACHED_MODEL = m.get("name", "").replace("models/", "")
                return CACHED_MODEL
    except Exception as e:
        print(e)
    return "gemini-2.5-flash"

def ask_gemini(text):
    model = get_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
    data = {"contents": [{"parts": [{"text": text}]}]}
    r = requests.post(url, json=data, timeout=30)
    if r.status_code != 200:
        return f"خطأ من جوجل: {r.status_code} - {r.text[:300]}"
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("اهلا بيك في ZENOVA AI\nصنعني Abdulrahman Ali")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "من صنعك" in update.message.text.lower() or "صنعك" in update.message.text.lower():
        await update.message.reply_text("صنعني Abdulrahman Ali")
        return
    await update.message.reply_text("ثواني نفكر...")
    reply = ask_gemini(update.message.text)
    await update.message.reply_text(reply)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
app.run_polling(drop_pending_updates=True)
