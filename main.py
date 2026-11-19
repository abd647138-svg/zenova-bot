import os, google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import io, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# باش Render ما يقولش No open ports
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

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

CREATOR = "Abdulrahman Ali"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"اهلا بيك في ZENOVA AI\nصنعني {CREATOR}\n\nابعثلي اي سؤال او ابعثلي صورة و نحللها لك.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "من صنعك" in text or "who made you" in text or "صنعك" in text:
        await update.message.reply_text(f"صنعني {CREATOR}")
        return
    try:
        res = model.generate_content(update.message.text)
        await update.message.reply_text(res.text)
    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        await update.message.reply_text("صار خطأ، عاود حاول.")

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تمام، نحلل في الصورة... ثواني")
    try:
        photo_file = await update.message.photo[-1].get_file()
        data = await photo_file.download_as_bytearray()
        img = Image.open(io.BytesIO(data))
        res = model.generate_content(["اشرح شن فيها هاذي الصورة بالتفصيل بالعربي", img])
        await update.message.reply_text(res.text)
    except Exception as e:
        print(f"PHOTO ERROR: {e}")
        await update.message.reply_text("ما قدرتش نحلل الصورة، عاود ابعتها.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
app.add_handler(MessageHandler(filters.PHOTO, photo))
app.run_polling()
