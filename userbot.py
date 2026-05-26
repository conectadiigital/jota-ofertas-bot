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

FILTROS = [
    # Cupons
    "cupom", "cupons",
    # Informática
    "notebook", "laptop", "macbook", "computador", "pc gamer", "monitor", "teclado",
    "mouse", "headset", "mousepad", "webcam", "impressora", "roteador",
    "cabo", "hub", "memória ram", "ssd", "hd", "processador", "placa mãe",
    "placa de vídeo", "gpu", "cpu", "fonte", "gabinete", "cooler",
    "water cooler", "pendrive", "no-break",
    # Eletrônicos
    "smartphone", "celular", "iphone", "samsung", "xiaomi", "motorola",
    "tablet", "ipad", "smartwatch", "fone de ouvido", "earphone", "airpods",
    "caixa de som", "câmera", "carregador", "bateria", "tv", "smart tv",
    "projetor",
    # Games
    "console", "playstation", "xbox", "nintendo", "switch",
    "controle", "joystick", "game", "jogo", "steam", "epic games",
    "headset gamer", "cadeira gamer", "monitor gamer",
    # Componentes
    "rtx", "gtx", "rx", "ryzen", "intel", "amd", "nvidia", "geforce",
    "radeon", "core i3", "core i5", "core i7", "core i9",
]
# =============================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)
client = TelegramClient("session", API_ID, API_HASH)


def eh_relevante(texto: str) -> bool:
    t = texto.lower()
    return any(filtro in t for filtro in FILTROS)


@client.on(events.NewMessage(chats=CANAIS))
async def handler(event):
    try:
        msg = event.message
        texto = msg.text or msg.caption or ""
        canal = event.chat.username or event.chat.title or "Desconhecido"

        if not texto:
            return

        if not eh_relevante(texto):
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
        text="🤖 <b>Userbot atualizado com filtros!</b>\n\n"
             "Monitorando 9 canais em tempo real\n"
             "✅ Filtro ativo: Cupons, Tecnologia, Informática, Games e Eletrônicos",
        parse_mode=ParseMode.HTML
    )
    log.info("Userbot rodando...")
    await client.run_until_disconnected()


with client:
    client.loop.run_until_complete(main())
