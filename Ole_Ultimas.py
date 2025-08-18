import os
import feedparser
from telegram import Bot
from dotenv import load_dotenv
import asyncio
from html import unescape
import re
from flask import Flask
import threading
import schedule
import time
import json

# Configurar Flask para mantener un servidor activo
app = Flask(__name__)

@app.route("/")
def home():
    return "¡El bot está en línea y funcionando!"

# Cargar variables de entorno
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_ERROR_CHANNEL = os.getenv("TELEGRAM_ERROR_CHANNEL")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or not TELEGRAM_ERROR_CHANNEL:
    raise ValueError("Variables de entorno no están correctamente configuradas en el archivo .env")

# Inicializar el bot de Telegram
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Lista para almacenar enlaces ya enviados
try:
    with open("enlaces.json", "r") as f:
        enlaces_enviados = set(json.load(f))
except FileNotFoundError:
    enlaces_enviados = set()

# RSS Feeds
RSS_FEEDS = {
    "Diario Olé": "http://www.ole.com.ar/rss/ultimas-noticias/"
}

# Función para obtener noticias nuevas
async def obtener_nuevas_noticias():
    nuevas_noticias = []
    for fuente, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entrada in feed.entries:
            link = entrada.link
            if link not in enlaces_enviados:
                enlaces_enviados.add(link)
                # Guardar inmediatamente en archivo
                with open("enlaces.json", "w") as f:
                    json.dump(list(enlaces_enviados), f)
                titulo = unescape(getattr(entrada, "title", "Sin título"))
                resumen = unescape(re.sub(r'<.*?>', '', getattr(entrada, "summary", "")))
                nuevas_noticias.append({
                    'titulo': titulo,
                    'resumen': resumen,
                    'link': link,
                    'fuente': fuente
                })
    return nuevas_noticias

# Función para enviar noticias
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
            asyncio.create_task(eliminar_mensaje(TELEGRAM_CHAT_ID, msg.message_id))
        except Exception as e:
            error_msg = f"Error al enviar el mensaje: {e}"
            print(error_msg)
            try:
                await bot.send_message(chat_id=TELEGRAM_ERROR_CHANNEL, text=error_msg)
            except:
                pass

# Función para eliminar mensajes luego de 24h
async def eliminar_mensaje(chat_id, message_id):
    await asyncio.sleep(86400)  # 24 horas
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass

# Función para enviar logs al canal de errores
async def enviar_log(log_message):
    try:
        await bot.send_message(chat_id=TELEGRAM_ERROR_CHANNEL, text=log_message)
    except Exception as e:
        print(f"Error al enviar log al canal de errores: {e}")

# Limpieza de caché cada 5 días
async def limpiar_cache():
    try:
        enlaces_enviados.clear()
        with open("enlaces.json", "w") as f:
            json.dump(list(enlaces_enviados), f)
        print("Caché limpiada exitosamente.")
        await bot.send_message(chat_id=TELEGRAM_ERROR_CHANNEL, text="La caché fue limpiada exitosamente.")
    except Exception as e:
        error_msg = f"Error al limpiar la caché: {e}"
        print(error_msg)
        try:
            await bot.send_message(chat_id=TELEGRAM_ERROR_CHANNEL, text=error_msg)
        except:
            pass

# Bucle de monitoreo de noticias
async def iniciar_bot():
    print("Bot de noticias iniciado correctamente...")
    while True:
        try:
            nuevas_noticias = await obtener_nuevas_noticias()
            if nuevas_noticias:
                await enviar_noticias_por_telegram(nuevas_noticias)
                log_message = f"{len(nuevas_noticias)} noticia(s) enviada(s)."
            else:
                log_message = "No hay noticias nuevas."
            print(log_message)
            await enviar_log(log_message)
        except Exception as e:
            error_msg = f"Error durante el monitoreo: {e}"
            print(error_msg)
            await enviar_log(error_msg)
        await asyncio.sleep(300)  # 5 minutos

# Hilo para Flask
def iniciar_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

# Hilo para tareas programadas
def iniciar_schedule():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    schedule.every(5).days.do(lambda: loop.create_task(limpiar_cache()))
    while True:
        schedule.run_pending()
        time.sleep(60)

# Punto de entrada
if __name__ == "__main__":
    threading.Thread(target=iniciar_flask).start()
    threading.Thread(target=iniciar_schedule).start()
    asyncio.run(iniciar_bot())
