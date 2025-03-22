import os
import feedparser
from telegram import Bot
from dotenv import load_dotenv
import asyncio
from html import unescape
import re
from flask import Flask

# Configurar Flask para mantener un servidor activo
app = Flask(__name__)

@app.route("/")
def home():
    return "¡El bot está en línea y funcionando!"

# Cargar variables de entorno
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no están configurados en el archivo .env")

# Inicializar el bot de Telegram
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# URLs de feeds RSS
RSS_FEEDS = {
    "Diario Olé": "http://www.ole.com.ar/rss/ultimas-noticias/",
    "Infobae Deportes": "https://www.infobae.com/deportes/rss/"
}

# Almacena los enlaces de noticias ya enviadas
enviadas = set()

def limpiar_html(texto):
    texto_sin_html = re.sub(r'<[^>]+>', '', texto)  # Eliminar etiquetas HTML
    return unescape(texto_sin_html)  # Decodificar entidades HTML

def es_deportivo(titulo, resumen, link):
    palabras
