import os, requests, time
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

def ask_gemini(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={GEMINI_KEY}"
    data = {"contents": [{"parts": [{"text": text}]}]}
    for i in range(5):
        try:
            r = requests.post(url, json=data, timeout=30)
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
            if r.status_code == 503:
                time.sleep(5)
                continue
            return f"خطأ من جوجل: {r.status_code} - {r.text[:200]}"
        except:
            time.sleep(3)
            continue
    return "جوجل عليها زحمة هلبا توا، استنى 5 دقايق و عاود"

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
