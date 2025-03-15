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

# URL del feed RSS
RSS_URL = "http://www.ole.com.ar/rss/ultimas-noticias/"

# Almacena los enlaces de noticias ya enviadas
enviadas = set()

def limpiar_html(texto):
    texto_sin_html = re.sub(r'<[^>]+>', '', texto)  # Eliminar etiquetas HTML
    return unescape(texto_sin_html)  # Decodificar entidades HTML

async def obtener_nuevas_noticias():
    feed = feedparser.parse(RSS_URL)
    nuevas_noticias = []

    for entrada in feed.entries:  # Corrección de "en" a "in"
        if entrada.link not in enviadas:
            nuevas_noticias.append({
                "titulo": limpiar_html(entrada.title),
                "link": entrada.link,
                "resumen": limpiar_html(entrada.summary)
            })
            enviadas.add(entrada.link)

    return nuevas_noticias

async def enviar_noticias_por_telegram(nuevas_noticias):
    for noticia in nuevas_noticias:
        mensaje = f"*{noticia['titulo']}*\n\n{noticia['resumen']}\n\n[Leer más]({noticia['link']})\n\n📡 *Fuente: Diario Olé*"
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensaje, parse_mode="Markdown")
        except Exception as e:
            print(f"Error al enviar el mensaje: {e}")

async def iniciar_bot():
    print("Bot de noticias iniciado correctamente...")

    while True:
        try:
            nuevas_noticias = await obtener_nuevas_noticias()
            if nuevas_noticias:
                await enviar_noticias_por_telegram(nuevas_noticias)
                print(f"{len(nuevas_noticias)} noticia(s) enviada(s).")
            else:
                print("No hay noticias nuevas.")
        except Exception as e:
            print(f"Error durante el monitoreo: {e}")

        await asyncio.sleep(300)  # Esperar 5 minutos

if __name__ == "__main__":
    # Ejecutar Flask y el bot en paralelo
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)).start()
    asyncio.run(iniciar_bot())

