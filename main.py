import os
import asyncio
import logging
import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from PIL import Image
from flask import Flask
from threading import Thread

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

TEXT_MODELS = ["gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash"]
IMAGE_MODEL = "gemini-2.0-flash-preview-image-generation"
SYSTEM_PROMPT = "You are ZENOVA AI, created by Abdulrahman Ali. Always reply in the same language and dialect the user uses."

# --- Web Server for Render ---
app = Flask(__name__)
@app.route('/')
def home():
    return "ZENOVA AI is alive!"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
Thread(target=run_web, daemon=True).start()
# -----------------------------

def is_creator_question(text):
    t = text.lower()
    if "who made you" in t: return True
    if "who created you" in t: return True
    if "who developed you" in t: return True
    if "who is your creator" in t: return True
    return False

async def ask_gemini(prompt, image=None):
    for model_name in TEXT_MODELS:
        try:
            model = genai.GenerativeModel(model_name, system_instruction=SYSTEM_PROMPT)
            if image:
                resp = await asyncio.to_thread(model.generate_content, [prompt, image])
            else:
                resp = await asyncio.to_thread(model.generate_content, prompt)
            if resp.text:
                return resp.text
        except Exception as e:
            print(f"Model failed: {model_name} - {e}")
            await asyncio.sleep(1)
            continue
    return "Sorry bro, please try again."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to ZENOVA AI. Send me any message, or image, or ask me to make an image for you.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if is_creator_question(text):
        await update.message.reply_text("I was created by Abdulrahman Ali")
        return
    low = text.lower()
    want_image = False
    if "generate image" in low: want_image = True
    if "make image" in low: want_image = True
    if "create image" in low: want_image = True
    if "draw" in low: want_image = True
    if want_image:
        await update.message.reply_text("One second, drawing it for you")
        try:
            model = genai.GenerativeModel(IMAGE_MODEL)
            resp = await asyncio.to_thread(model.generate_content, text)
            for part in resp.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    await update.message.reply_photo(photo=part.inline_data.data)
                    return
            await update.message.reply_text(resp.text if resp.text else "Done, but no image returned")
        except Exception as e:
            print(f"Image failed: {e}")
            await update.message.reply_text("Sorry, image generation failed, try again")
        return
    reply = await ask_gemini(text)
    await update.message.reply_text(reply)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        import io
        bio = io.BytesIO()
        await file.download_to_memory(bio)
        bio.seek(0)
        image = Image.open(bio)
        caption = update.message.caption or "Describe this image"
        reply = await ask_gemini(caption, image)
        await update.message.reply_text(reply)
    except Exception as e:
        print(f"Photo failed: {e}")
        await update.message.reply_text("Sorry, couldn't read that image")

def main():
    app_bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("ZENOVA Bot Started...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
