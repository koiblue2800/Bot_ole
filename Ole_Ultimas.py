import os
import feedparser
from telegram import Bot
from dotenv import load_dotenv
import asyncio
from html import unescape
import re

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
    """
    Limpia etiquetas HTML y convierte entidades como &amp; en texto plano.
    """
    texto_sin_html = re.sub(r'<[^>]+>', '', texto)  # Eliminar etiquetas HTML
    return unescape(texto_sin_html)  # Decodificar entidades HTML

async def obtener_nuevas_noticias():
    """
    Obtiene las noticias nuevas desde el feed RSS.
    """
    feed = feedparser.parse(RSS_URL)
    nuevas_noticias = []

    for entrada in feed.entries:
        # Verifica si la noticia ya fue enviada
        if entrada.link not in enviadas:
            nuevas_noticias.append({
                "titulo": limpiar_html(entrada.title),
                "link": entrada.link,
                "resumen": limpiar_html(entrada.summary)
            })
            enviadas.add(entrada.link)

    return nuevas_noticias

async def enviar_noticias_por_telegram(nuevas_noticias):
    """
    Envía noticias nuevas por Telegram.
    """
    for noticia in nuevas_noticias:
        mensaje = f"*{noticia['titulo']}*\n\n{noticia['resumen']}\n\n[Leer más]({noticia['link']})\n\n📡 *Fuente: Diario Olé*"
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensaje, parse_mode="Markdown")
        except Exception as e:
            print(f"Error al enviar el mensaje: {e}")

async def main():
    """
    Monitorea el feed RSS y envía actualizaciones periódicas.
    """
    print("Bot de noticias iniciado correctamente...")

    while True:
        try:
            # Obtener noticias nuevas
            nuevas_noticias = await obtener_nuevas_noticias()
            if nuevas_noticias:
                await enviar_noticias_por_telegram(nuevas_noticias)
                print(f"{len(nuevas_noticias)} noticia(s) enviada(s).")
            else:
                print("No hay noticias nuevas.")
        except Exception as e:
            print(f"Error durante el monitoreo: {e}")

        await asyncio.sleep(300)  # Esperar 5 minutos antes de consultar nuevamente

if __name__ == "__main__":
    asyncio.run(main())

