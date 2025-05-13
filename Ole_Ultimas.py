import os
import feedparser
from telegram import Bot
from dotenv import load\_dotenv
import asyncio
from html import unescape
import re
from flask import Flask
import threading
import schedule
import time

# Configurar Flask para mantener un servidor activo

app = Flask(**name**)

@app.route("/")
def home():
return "¡El bot está en línea y funcionando!"

# Cargar variables de entorno

load\_dotenv()
TELEGRAM\_BOT\_TOKEN = os.getenv("TELEGRAM\_BOT\_TOKEN")
TELEGRAM\_CHAT\_ID = os.getenv("TELEGRAM\_CHAT\_ID")
TELEGRAM\_ERROR\_CHANNEL = os.getenv("TELEGRAM\_ERROR\_CHANNEL")

if not TELEGRAM\_BOT\_TOKEN or not TELEGRAM\_CHAT\_ID or not TELEGRAM\_ERROR\_CHANNEL:
raise ValueError("Variables de entorno no están correctamente configuradas en el archivo .env")

# Inicializar el bot de Telegram

bot = Bot(token=TELEGRAM\_BOT\_TOKEN)

# Lista para almacenar enlaces ya enviados

enlaces\_enviados = set()

# RSS Feeds

RSS\_FEEDS = {
"Diario Olé": "[http://www.ole.com.ar/rss/ultimas-noticias/](http://www.ole.com.ar/rss/ultimas-noticias/)"
}

# Función para obtener noticias nuevas

async def obtener\_nuevas\_noticias():
nuevas\_noticias = \[]
for fuente, url in RSS\_FEEDS.items():
feed = feedparser.parse(url)
for entrada in feed.entries:
link = entrada.link
if link not in enlaces\_enviados:
enlaces\_enviados.add(link)
titulo = unescape(entrada.title)
resumen = unescape(re.sub(r'<.\*?>', '', entrada.summary))
nuevas\_noticias.append({
'titulo': titulo,
'resumen': resumen,
'link': link,
'fuente': fuente
})
return nuevas\_noticias

# Función para enviar noticias

async def enviar\_noticias\_por\_telegram(nuevas\_noticias):
for noticia in nuevas\_noticias:
mensaje = (
f"*{noticia\['titulo']}*\n\n"
f"{noticia\['resumen']}\n\n"
f"[Leer más]({noticia['link']})\n\n"
f"📡 *Fuente: {noticia\['fuente']}*"
)
try:
msg = await bot.send\_message(chat\_id=TELEGRAM\_CHAT\_ID, text=mensaje, parse\_mode="Markdown")
asyncio.create\_task(eliminar\_mensaje(TELEGRAM\_CHAT\_ID, msg.message\_id))
except Exception as e:
error\_msg = f"Error al enviar el mensaje: {e}"
print(error\_msg)
try:
await bot.send\_message(chat\_id=TELEGRAM\_ERROR\_CHANNEL, text=error\_msg)
except:
pass

# Función para eliminar mensajes luego de 24h

async def eliminar\_mensaje(chat\_id, message\_id):
await asyncio.sleep(86400)  # 24 horas
try:
await bot.delete\_message(chat\_id=chat\_id, message\_id=message\_id)
except Exception as e:
error\_msg = f"Error al eliminar el mensaje: {e}"
print(error\_msg)
try:
await bot.send\_message(chat\_id=TELEGRAM\_ERROR\_CHANNEL, text=error\_msg)
except:
pass

# Limpieza de caché cada 5 días

async def limpiar\_cache():
try:
enlaces\_enviados.clear()  # Ahora sí limpia algo real
print("Caché limpiada exitosamente.")
await bot.send\_message(chat\_id=TELEGRAM\_ERROR\_CHANNEL, text="La caché fue limpiada exitosamente.")
except Exception as e:
error\_msg = f"Error al limpiar la caché: {e}"
print(error\_msg)
try:
await bot.send\_message(chat\_id=TELEGRAM\_ERROR\_CHANNEL, text=error\_msg)
except:
pass

# Bucle de monitoreo de noticias

async def iniciar\_bot():
print("Bot de noticias iniciado correctamente...")
while True:
try:
nuevas\_noticias = await obtener\_nuevas\_noticias()
if nuevas\_noticias:
await enviar\_noticias\_por\_telegram(nuevas\_noticias)
print(f"{len(nuevas\_noticias)} noticia(s) enviada(s).")
else:
print("No hay noticias nuevas.")
except Exception as e:
error\_msg = f"Error durante el monitoreo: {e}"
print(error\_msg)
try:
await bot.send\_message(chat\_id=TELEGRAM\_ERROR\_CHANNEL, text=error\_msg)
except:
pass
await asyncio.sleep(300)  # 5 minutos

# Hilo para Flask

def iniciar\_flask():
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

# Hilo para tareas programadas

def iniciar\_schedule():
loop = asyncio.new\_event\_loop()
asyncio.set\_event\_loop(loop)
schedule.every(5).days.do(lambda: loop.create\_task(limpiar\_cache()))
while True:
schedule.run\_pending()
time.sleep(60)

# Punto de entrada

if **name** == "**main**":
threading.Thread(target=iniciar\_flask).start()
threading.Thread(target=iniciar\_schedule).start()
asyncio.run(iniciar\_bot())
