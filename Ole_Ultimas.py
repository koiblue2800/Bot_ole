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

# URL del feed RSS del Diario Olé
RSS_FEEDS = {
    "Diario Olé": "http://www.ole.com.ar/rss/ultimas-noticias/"
}

# Almacena los enlaces de noticias ya enviadas
enlaces_enviados = set()

async def obtener_nuevas_noticias():
    nuevas_noticias = []
    for fuente, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entrada in feed.entries:
            link = entrada.link
            if link not in enlaces_enviados:
                enlaces_enviados.add(link)
                titulo = unescape(entrada.title)
                resumen = unescape(re.sub(r'<.*?>', '', entrada.summary))  # Eliminar etiquetas HTML
                nuevas_noticias.append({
                    'titulo': titulo,
                    'resumen': resumen,
                    'link': link,
                    'fuente': fuente
                })
    return nuevas_noticias

async def enviar_noticias_por_telegram(nuevas_noticias):
    for noticia in nuevas_noticias:
        mensaje = (
            f"*{noticia['titulo']}*\n\n"
            f"{noticia['resumen']}\n\n"
            f"[Leer más]({noticia['link']})\n\n"
            f"📡 *Fuente: {noticia['fuente']}*"
        )
        try:
            msg = await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensaje, parse_mode="Markdown")
            # Programar eliminación del mensaje después de un día
            asyncio.create_task(eliminar_mensaje(TELEGRAM_CHAT_ID, msg.message_id))
        except Exception as e:
            print(f"Error al enviar el mensaje: {e}")

async def eliminar_mensaje(chat_id, message_id):
    await asyncio.sleep(86400)  # Espera 24 horas (86400 segundos)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Error al eliminar el mensaje: {e}")

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
