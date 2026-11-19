import os
import io
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import google.generativeai as genai
from PIL import Image

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

TEXT_MODELS = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

IMAGE_MODEL = "gemini-2.0-flash-preview-image-generation"

SYSTEM_PROMPT = "You are ZENOVA AI, created by Abdulrahman Ali. Always reply in the same language and dialect the user used. If user writes Libyan Arabic, reply Libyan Arabic. If user asks who made you, answer only: Abdulrahman Ali. Be friendly and short. If user sends image, analyze it."

def is_creator_question(text):
    t = text.lower()
    if "who made you" in t:
        return True
    if "who created you" in t:
        return True
    if "who developed you" in t:
        return True
    if "who is your creator" in t:
        return True
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
    return "Busy now, please try again"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "Welcome to ZENOVA AI. Send me any message, or image, or ask me to make an image for you."
    await update.message.reply_text(msg)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if is_creator_question(text):
        await update.message.reply_text("I was created by Abdulrahman Ali")
        return

    low = text.lower()
    want_image = False
    if "generate image" in low:
        want_image = True
    if "make image" in low:
        want_image = True
    if "create image" in low:
        want_image = True
    if "draw" in low:
        want_image = True

    if want_image:
        await update.message.reply_text("One second, drawing it for you")
        try:
            model = genai.GenerativeModel(IMAGE_MODEL)
            resp = await asyncio.to_thread(model.generate_content, f"Generate image: {text}")
            for part in resp.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    await update.message.reply_photo(photo=io.BytesIO(part.inline_data.data))
                    return
            await update.message.reply_text("Could not draw it now, try another description")
        except Exception as e:
            print(e)
            await update.message.reply_text("Image generation is busy, try in a minute")
        return

    await update.message.reply_text("One second thinking")
    answer = await ask_gemini(text)
    await update.message.reply_text(answer)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.caption or "What is in this image?"
    await update.message.reply_text("Got the image, analyzing it now")
    try:
        photo = await update.message.photo[-1].get_file()
        bio = io.BytesIO()
        await photo.download_to_memory(bio)
        bio.seek(0)
        img = Image.open(bio)
        answer = await ask_gemini(caption, image=img)
        await update.message.reply_text(answer)
    except Exception as e:
        print(e)
        await update.message.reply_text("Could not read the image, please send again")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("ZENOVA AI Started")
    app.run_polling()

if __name__ == "__main__":
    main()
