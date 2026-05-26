import asyncio
import logging
from telethon import TelegramClient, events
from telegram import Bot
from telegram.constants import ParseMode

# =============================================
# CONFIGURAÇÕES
# =============================================
API_ID = 35990342
API_HASH = "a5e4b989566d3110d9756a27363b7004"
TELEGRAM_TOKEN = "8928368941:AAG8FAM49Wj71HixaMyaoFK1qXGQN8FvLEo"
TELEGRAM_CHAT_ID = "656910452"

# Canais oficiais de ofertas
CANAIS = [
    "pelandobr",
    "cupons_desconto",
    "peperaiohardware",
    "ofertasgamer_oficial",
    "lapromotion",
    "sharkdaspromo",
    "promocoesecuponsglobais",
    "tecnoarthardware",
    "promotop",
]
# =============================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)
client = TelegramClient("session", API_ID, API_HASH)


@client.on(events.NewMessage(chats=CANAIS))
async def handler(event):
    try:
        msg = event.message
        texto = msg.text or msg.caption or ""
        canal = event.chat.username or event.chat.title or "Desconhecido"

        if not texto:
            return

        mensagem = (
            f"🔔 <b>Nova oferta de @{canal}!</b>\n\n"
            f"{texto[:800]}"
        )

        if msg.photo:
            await bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=await client.download_media(msg.photo, bytes),
                caption=mensagem,
                parse_mode=ParseMode.HTML
            )
        else:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=mensagem,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False
            )

        log.info(f"Oferta de @{canal} enviada!")

    except Exception as e:
        log.error(f"Erro ao processar mensagem: {e}")


async def main():
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text="🤖 <b>Userbot atualizado!</b>\n\n"
             "Monitorando canais em tempo real:\n"
             "🔥 @pelandobr\n"
             "⚡ @cupons_desconto\n"
             "🖥️ @peperaiohardware\n"
             "🎮 @ofertasgamer_oficial\n"
             "🛒 @lapromotion\n"
             "🦈 @sharkdaspromo\n"
             "🌍 @promocoesecuponsglobais\n"
             "💻 @tecnoarthardware\n"
             "🚀 @promotop\n",
        parse_mode=ParseMode.HTML
    )
    log.info("Userbot rodando...")
    await client.run_until_disconnected()


with client:
    client.loop.run_until_complete(main())
