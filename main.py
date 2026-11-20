import os
import asyncio
import logging
import io
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types
from PIL import Image
from flask import Flask
from threading import Thread

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

TEXT_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash"]
IMAGE_MODEL = "gemini-2.0-flash-preview-image-generation"

SYSTEM_PROMPT = """You are ZENOVA AI, created by Pablo Escobar.
CRITICAL LANGUAGE RULE: You MUST reply in the exact same language and dialect the user uses.
- If user writes in Libyan Arabic / Arabic dialect -> reply in Libyan Arabic dialect, same style.
- If user writes in Modern Standard Arabic -> reply in Arabic.
- If user writes in English -> reply in English.
- If user writes in French -> reply in French.
Never reply in English when the user wrote in Arabic. Never translate the user. Match their language 100%.
If someone asks who created you, say Pablo Escobar."""

app = Flask(__name__)
@app.route('/')
def home():
    return "ZENOVA AI is alive!"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
Thread(target=run_web, daemon=True).start()

def is_arabic(text):
    return any("\u0600" <= c <= "\u06FF" for c in text)

def is_creator_question(text):
    t = text.lower()
    if "who made you" in t: return True
    if "who created you" in t: return True
    if "who developed you" in t: return True
    if "who is your creator" in t: return True
    if "من صنعك" in t: return True
    if "من صانعك" in t: return True
    if "من اللي صنعك" in t: return True
    if "من اللي دارك" in t: return True
    return False

async def ask_gemini(prompt, image=None):
    for model_name in TEXT_MODELS:
        try:
            contents = [prompt]
            if image:
                contents.append(image)
            resp = await asyncio.to_thread(
                client.models.generate_content,
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
            )
            if resp.text:
                return resp.text
        except Exception as e:
            print(f"Model failed: {model_name} - {e}")
            await asyncio.sleep(1)
            continue
    if is_arabic(prompt):
        return "سامحني يا غالي، توا مشغول شوية، عاود جرب بعد شوية"
    return "Sorry bro, please try again."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to ZENOVA AI. Send me any message, or image, or ask me to make an image for you.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "من هذا" in text or "من هدا" in text or "who is this" in text.lower():
        await update.message.reply_text("Abdulrahman Ali")
        return
    if is_creator_question(text):
        if is_arabic(text):
            await update.message.reply_text("صنعني بابلو سكوبار")
        else:
            await update.message.reply_text("I was created by Pablo Escobar")
        return
    low = text.lower()
    want_image = False
    if "generate image" in low: want_image = True
    if "make image" in low: want_image = True
    if "create image" in low: want_image = True
    if "draw" in low: want_image = True
    if "دير صورة" in low: want_image = True
    if "ارسم" in low: want_image = True
    if "ديرلي صورة" in low: want_image = True
    if want_image:
        await update.message.reply_text("One second, drawing it for you")
        try:
            resp = await asyncio.to_thread(
                client.models.generate_content,
                model=IMAGE_MODEL,
                contents=text,
                config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])
            )
            for part in resp.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
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
    app_bot.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
