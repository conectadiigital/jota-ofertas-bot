import logging
import re
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telegram import Bot
from telegram.constants import ParseMode

# =============================================
# CONFIGURAÇÕES
# =============================================
API_ID = 35990342
API_HASH = "a5e4b989566d3110d9756a27363b7004"
TELEGRAM_TOKEN = "8928368941:AAG8FAM49Wj71HixaMyaoFK1qXGQN8FvLEo"
TELEGRAM_CHAT_ID = "-1003972490387"  # Grupo — ofertas vão aqui
TELEGRAM_OWNER_ID = "656910452"      # Você — avisos do bot vão aqui

ANTI_DUPLICATA_MINUTOS = 5

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
    "fadadoscupons",
]

CANAIS_SEM_FILTRO = [
    "fadadoscupons",
]

NOMES_CANAIS = {
    "pelandobr":               "🔥 Pelando BR",
    "cupons_desconto":         "🎟️ Cupons Desconto",
    "peperaiohardware":        "🖥️ Peperaio Hardware",
    "ofertasgamer_oficial":    "🎮 Ofertas Gamer",
    "lapromotion":             "💰 La Promotion",
    "sharkdaspromo":           "🦈 Shark das Promos",
    "promocoesecuponsglobais": "🌎 Promoções e Cupons Globais",
    "tecnoarthardware":        "⚙️ Tecnoart Hardware",
    "promotop":                "🏆 Promo Top",
    "fadadoscupons":           "🧚 Fada dos Cupons",
}

FILTROS = [
    # Informática
    "notebook", "laptop", "macbook", "computador", "pc gamer", "monitor", "teclado",
    "mouse", "headset", "mousepad", "webcam", "impressora", "roteador",
    "hub", "memória ram", "ssd", "hd", "processador", "placa mãe",
    "placa de vídeo", "gpu", "cpu", "fonte", "gabinete", "cooler",
    "water cooler", "pendrive", "no-break",
    # Eletrônicos
    "smartphone", "celular", "iphone", "samsung", "xiaomi", "motorola",
    "tablet", "ipad", "smartwatch", "fone de ouvido", "earphone", "airpods",
    "caixa de som", "câmera", "carregador", "bateria", "tv", "smart tv",
    "projetor", "ar-condicionado", "ar condicionado",
    "fire tv stick", "roku streaming",
    # Games
    "console", "playstation", "xbox", "nintendo", "switch",
    "controle", "joystick", "game", "steam", "epic games",
    "headset gamer", "cadeira gamer", "monitor gamer",
    # Componentes
    "rtx", "gtx", "ryzen", "intel", "amd", "nvidia", "geforce",
    "radeon", "core i3", "core i5", "core i7", "core i9",
]

BLOQUEIOS = [
    # Moda e vestuário
    "tênis", "camiseta", "blusa", "camisa", "roupa", "calçado",
    "sandália", "chinelo", "meia", "bermuda", "shorts", "calça",
    "vestido", "saia", "jaqueta", "moletom", "agasalho", "uniforme",
    "bolsa", "carteira", "cinto", "boné", "chapéu",
    # Beleza e cosméticos
    "perfume", "maquiagem", "batom", "shampoo", "condicionador",
    "protetor solar", "fps", "hidratante", "creme", "sérum",
    "desodorante", "sabonete", "esmalte", "base", "máscara",
    # Pet
    "cachorro", "gato", "pet", "ração", "coleira",
    "aquário", "pássaro", "hamster",
    # Brinquedos
    "brinquedo", "boneca", "pelúcia", "massinha", "lego",
    # Casa / Cama / Banho
    "edredom", "travesseiro", "lençol", "toalha", "tapete",
    "cortina", "almofada", "cobertor",
    # Bebê e infantil
    "fralda", "fraldas", "pampers", "bebê", "bebe",
    "infantil", "criança", "mamadeira", "chupeta",
    # Cozinha
    "panela", "panelas", "frigideira", "wok", "caçarola",
    "antiaderente", "cerâmico", "utensílio", "escorredor",
    "liquidificador", "batedeira", "mixer", "airfryer", "air fryer",
    "cafeteira", "chaleira", "forno", "micro-ondas", "microondas",
    "talheres", "prato", "tigela", "xícara", "copo",
]
# =============================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)
client = TelegramClient("session", API_ID, API_HASH)

# Histórico anti-duplicata: {chave: datetime}
historico_enviados = {}


def extrair_links(texto: str):
    return re.findall(r'https?://\S+', texto)


def extrair_palavras_chave(texto: str):
    ignorar = {"para", "com", "por", "mais", "valor", "oferta", "promo", "desc"}
    palavras = re.findall(r'\b\w{4,}\b', texto.lower())
    return {p for p in palavras if p not in ignorar}


def eh_duplicata(texto: str) -> bool:
    agora = datetime.now()
    limite = agora - timedelta(minutes=ANTI_DUPLICATA_MINUTOS)

    # Limpa histórico antigo
    expirados = [k for k, v in historico_enviados.items() if v < limite]
    for k in expirados:
        del historico_enviados[k]

    # Verifica por link
    links = extrair_links(texto)
    for link in links:
        if link in historico_enviados:
            log.info(f"Duplicata detectada por link: {link}")
            return True

    # Verifica por palavras-chave do título (primeira linha)
    primeira_linha = texto.split('\n')[0].strip()
    palavras = extrair_palavras_chave(primeira_linha)
    chave_titulo = " ".join(sorted(palavras))
    if chave_titulo and chave_titulo in historico_enviados:
        log.info(f"Duplicata detectada por título: {chave_titulo}")
        return True

    # Registra no histórico
    for link in links:
        historico_enviados[link] = agora
    if chave_titulo:
        historico_enviados[chave_titulo] = agora

    return False


def eh_relevante(texto: str) -> bool:
    t = texto.lower()
    return any(filtro in t for filtro in FILTROS)


def eh_bloqueado(texto: str) -> bool:
    t = texto.lower()
    return any(bloqueio in t for bloqueio in BLOQUEIOS)


@client.on(events.NewMessage(chats=CANAIS))
async def handler(event):
    try:
        msg = event.message
        texto = msg.text or msg.caption or ""
        canal_username = (event.chat.username or "").lower()
        nome_exibido = NOMES_CANAIS.get(canal_username, event.chat.title or canal_username or "Desconhecido")

        if not texto:
            return

        # Fada dos Cupons passa tudo sem filtro e sem bloqueio
        if canal_username in CANAIS_SEM_FILTRO:
            pass
        else:
            if eh_bloqueado(texto):
                return
            if not eh_relevante(texto):
                return

        # Anti-duplicata
        if eh_duplicata(texto):
            return

        mensagem = (
            f"🔔 <b>JJ Ofertas</b>\n\n"
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

        log.info(f"Oferta de {nome_exibido} enviada!")

    except Exception as e:
        log.error(f"Erro ao processar mensagem: {e}")


async def main():
    await bot.send_message(
        chat_id=TELEGRAM_OWNER_ID,
        text=(
            "🤖 <b>JJ Ofertas Bot — Online!</b>\n\n"
            "📡 Monitorando 10 canais em tempo real\n"
            "🎯 Filtros: Informática · Eletrônicos · Games · Componentes\n"
            "🧚 Fada dos Cupons: todas as ofertas sem filtro e sem bloqueio\n"
            "🚫 Bloqueios: Moda · Beleza · Pet · Brinquedos · Casa · Bebê · Cozinha\n"
            "🔄 Anti-duplicata: 5 minutos"
        ),
        parse_mode=ParseMode.HTML
    )
    log.info("Userbot rodando...")
    await client.run_until_disconnected()


with client:
    client.loop.run_until_complete(main())
