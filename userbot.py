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
TELEGRAM_TOKEN = "8625612683:AAEc3prPY2VqtAF6s9u-agrPE7BdM6SuFDA"
TELEGRAM_CHAT_ID = "-1003923063277"  # Canal JOTA OFERTAS
TELEGRAM_OWNER_ID = "8889687119"     # Você — avisos do bot vão aqui

ANTI_DUPLICATA_MINUTOS = 5
ANTI_DUPLICATA_PALAVRAS = 3

CANAIS = [
    "pelandobr",
    "cupons_desconto",
    "peperaiohardware",
    "ofertasgamer_oficial",
    "lapromotion",
    "sharkdaspromo",
    "tecnoarthardware",
    "promotop",
    "fadadoscupons",
    "BenchPromos",
    "TJGOFERTASs",
    "pcdofafapromo",
]

CANAIS_SEM_FILTRO = [
    "fadadoscupons",
]

NOMES_CANAIS = {
    "pelandobr":            "🔥 Pelando BR",
    "cupons_desconto":      "🎟️ Cupons Desconto",
    "peperaiohardware":     "🖥️ Peperaio Hardware",
    "ofertasgamer_oficial": "🎮 Ofertas Gamer",
    "lapromotion":          "💰 La Promotion",
    "sharkdaspromo":        "🦈 Shark das Promos",
    "tecnoarthardware":     "⚙️ Tecnoart Hardware",
    "promotop":             "🏆 Promo Top",
    "fadadoscupons":        "🧚 Fada dos Cupons",
    "benchpromos":          "🖥️ Bench Promos",
    "tjgofertass":          "🛒 TJG Ofertas",
    "pcdofafapromo":        "💻 PC do Fafa Promo",
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
    "body spray", "desodorante spray", "body lotion", "body cream",
    "boticário", "o boticário", "floratta", "egeo",
    "loção", "gel", "tônico", "micellar", "água micelar",
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
    # Alimentos
    "macarrão", "massa", "arroz", "feijão", "farinha", "açúcar",
    "café", "leite", "queijo", "iogurte", "manteiga", "margarina",
    "óleo", "azeite", "molho", "tempero", "sal", "pimenta",
    "biscoito", "bolacha", "chocolate", "bala", "sorvete",
    "suco", "refrigerante", "água", "cerveja", "vinho",
    "carne", "frango", "peixe", "presunto", "salsicha",
    "fruta", "verdura", "legume", "alho", "cebola",
    "urbano", "gluten", "espinafre", "kids",
    # Ferramentas
    "furadeira", "parafusadeira", "serra", "esmerilhadeira",
    "martelo", "chave de fenda", "alicate", "nível",
    "trena", "fita métrica", "escada", "carrinho de mão",
    "compressor", "lavadora de pressão", "mangueira",
    "maleta de ferramentas", "kit ferramentas", "bancada",
    "lixadeira", "tupia", "mandril", "broca",
]

CORTAR_A_PARTIR_DE = [
    "participe do nosso",
    "participe do meu",
    "nosso outro grupo",
    "nosso grupo de ofertas",
    "promoções no whatsapp",
    "promoções gerais",
    "entre no nosso",
    "entre no meu",
    "acesse nosso canal",
    "acesse nosso grupo",
    "siga nosso canal",
    "whatsapp.com/channel",
    "link pra entrar no grupo",
    "link para entrar no grupo",
    "#anúncio",
    "#anuncio",
]
# =============================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)
client = TelegramClient("jotaofertas", API_ID, API_HASH)

historico_enviados = {}

PALAVRAS_IGNORAR = {
    "para", "com", "por", "mais", "valor", "oferta", "promo", "desc",
    "sem", "fio", "the", "and", "box", "new", "und", "unid", "unidade",
    "kit", "cor", "preto", "branco", "azul", "verde", "vermelho", "rosa",
    "cinza", "novo", "nova", "lacrado", "lacrada", "original", "oficial",
    "garantia", "anos", "ano", "meses", "gratis", "free", "plus", "pro",
    "max", "mini", "ultra", "series", "serie", "edition", "versao",
}


def cortar_propaganda(texto: str) -> str:
    t_lower = texto.lower()
    for frase in CORTAR_A_PARTIR_DE:
        idx = t_lower.find(frase)
        if idx != -1:
            texto = texto[:idx].strip()
    return texto


def limpar_texto(texto: str) -> str:
    texto = re.sub(r'[^\w\s]', ' ', texto, flags=re.UNICODE)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto.lower()


def extrair_palavras_chave(texto: str) -> set:
    texto = limpar_texto(texto)
    palavras = re.findall(r'\b\w{3,}\b', texto)
    return {p for p in palavras if p not in PALAVRAS_IGNORAR}


def extrair_links(texto: str) -> list:
    return re.findall(r'https?://\S+', texto)


def similaridade(palavras1: set, palavras2: set) -> int:
    return len(palavras1 & palavras2)


def eh_duplicata(texto: str) -> bool:
    agora = datetime.now()
    limite = agora - timedelta(minutes=ANTI_DUPLICATA_MINUTOS)

    expirados = [k for k, v in historico_enviados.items() if v < limite]
    for k in expirados:
        del historico_enviados[k]

    links = extrair_links(texto)
    for link in links:
        if link in historico_enviados:
            log.info(f"Duplicata detectada por link: {link}")
            return True

    linhas = [l.strip() for l in texto.split('\n') if l.strip()]
    primeira_linha = linhas[0] if linhas else ""
    palavras_novas = extrair_palavras_chave(primeira_linha)

    for chave in list(historico_enviados.keys()):
        if chave.startswith("titulo:"):
            palavras_hist = set(chave.replace("titulo:", "").split())
            if similaridade(palavras_novas, palavras_hist) >= ANTI_DUPLICATA_PALAVRAS:
                log.info(f"Duplicata detectada por similaridade: {palavras_novas & palavras_hist}")
                return True

    for link in links:
        historico_enviados[link] = agora
    if palavras_novas:
        chave_titulo = "titulo:" + " ".join(sorted(palavras_novas))
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

        texto = cortar_propaganda(texto)

        if not texto:
            return

        if canal_username in CANAIS_SEM_FILTRO:
            pass
        else:
            if eh_bloqueado(texto):
                return
            if not eh_relevante(texto):
                return

        if eh_duplicata(texto):
            return

        mensagem = (
            f"🔔 <b>JOTA Ofertas</b>\n\n"
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
            "🤖 <b>JOTA Ofertas Bot — Online!</b>\n\n"
            "📡 Monitorando 12 canais em tempo real\n"
            "🎯 Filtros: Informática · Eletrônicos · Games · Componentes\n"
            "🧚 Fada dos Cupons: todas as ofertas sem filtro e sem bloqueio\n"
            "🚫 Bloqueios: Moda · Beleza · Pet · Brinquedos · Casa · Bebê · Cozinha · Alimentos · Ferramentas\n"
            "🔄 Anti-duplicata: 5 minutos · 3 palavras\n"
            "✂️ Corte automático de propaganda"
        ),
        parse_mode=ParseMode.HTML
    )
    log.info("Userbot rodando...")
    await client.run_until_disconnected()


with client:
    client.loop.run_until_complete(main())
