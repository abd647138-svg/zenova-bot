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

CREATOR_NAME = "Abdulrahman Ali"

SYSTEM_PROMPT = """
You are ZENOVA AI, created by Abdulrahman Ali.
Rules:
1. Always reply in the same language and dialect the user used.
2. If user asks who made you, answer only: Abdulrahman Ali.
3. Be friendly and short.
4. If user sends image, analyze it and answer what is asked.
"""

def is_arabic(text):
    for ch in text:
        if "\u0600" <= ch <= "\u06FF":
            return True
    return False

def is_creator_question(text):
    t = text.lower()
    words = ["who made you", "who created you", "who developed you", "who is your creator"]
    for w in words:
        if w in t:
            return True
    if "
