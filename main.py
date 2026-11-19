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

SYSTEM_PROMPT = "You are ZENOVA AI, created by Abdulrahman Ali. Always reply in the same language and dialect the user used. If user asks who made you, answer only: Abdulrahman Ali. Be friendly and short. If user sends image, analyze it and answer what is asked."

def is_arabic(text):
    for ch in text:
        if 1536 <= ord(ch) <= 1791:
            return True
    return False

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
    if is_arabic(prompt):
        return "صار ضغط شوية، عاود ابعت رسالتك توا"
    return "Busy now, please try again"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "Welcome to ZENOVA AI. Send me any message, or image, or ask me to make an image for you."
    await update.message.reply_text(msg)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    arabic = is_arabic(text)

    if is_creator_question(text):
        if arabic:
            await update.message.reply_text("اللي صنعني هو عبدالرحمن علي")
        else:
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
    if "صورة" in text:
        want_image = True
    if "ارسم" in text:
        want_image = True
    if "ديرلي" in text:
        want_image = True

    if want_image:
        if arabic:
            await update.message.reply_text("ثواني نرسمهالك")
        else:
            await update.message.reply_text("One second, drawing it for you")
        try:
            model = genai.GenerativeModel(IMAGE_MODEL)
            resp = await asyncio.to_thread(model.generate_content, f"Generate image: {text}")
            for part in resp.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    await update.message.reply_photo(photo=io.BytesIO(part.inline_data.data))
                    return
            if arabic:
                await update.message.reply_text("ما قدرتش نرسمها توا، جرب وصف تاني")
            else:
                await update.message.reply_text("Could not draw it now, try another description")
        except Exception as e:
            print(e)
            if arabic:
                await update.message.reply_text("صار ضغط على توليد الصور، جرب بعد دقيقة")
            else:
                await update.message.reply_text("Image generation is busy, try in a minute")
        return

    if arabic:
        await update.message.reply_text("ثواني نفكر")
    else:
        await update.message.reply_text("One second thinking")
    answer = await ask_gemini(text)
    await update.message.reply_text(answer)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.caption or ""
    arabic = is_arabic(caption)
    if arabic:
        await update.message.reply_text("وصلتني الصورة، ثواني نحللها")
    else:
        await update.message.reply_text("Got the image, analyzing it now")
    try:
        photo = await update.message.photo[-1].get_file()
        bio = io.BytesIO()
        await photo.download_to_memory(bio)
        bio.seek(0)
        img = Image.open(bio)
        if caption == "":
            caption = "What is in this image?"
        answer = await ask_gemini(caption, image=img)
        await update.message.reply_text(answer)
    except Exception as e:
        print(e)
        if arabic:
            await update.message.reply_text("ما قدرتش نقرا الصورة توا، عاود ابعتها")
        else:
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
