import asyncio
import logging
import hashlib
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode

# =============================================
# CONFIGURAÇÕES
# =============================================
TELEGRAM_TOKEN = "8928368941:AAG8FAM49Wj71HixaMyaoFK1qXGQN8FvLEo"
TELEGRAM_CHAT_ID = "656910452"
INTERVALO_SEGUNDOS = 60
# =============================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)
VISTAS_FILE = "ofertas_vistas.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


def carregar_vistas() -> set:
    if os.path.exists(VISTAS_FILE):
        with open(VISTAS_FILE) as f:
            return set(json.load(f))
    return set()


def salvar_vistas(vistas: set):
    with open(VISTAS_FILE, "w") as f:
        json.dump(list(vistas), f)


@dataclass
class Oferta:
    titulo: str
    preco: str
    link: str
    fonte: str
    imagem: Optional[str] = None

    def id(self) -> str:
        return hashlib.md5(self.link.encode()).hexdigest()


async def buscar_pelando_rss(client):
    ofertas = []
    try:
        r = await client.get("https://www.pelando.com.br/feed/deals", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:30]:
                titulo = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                if not titulo or not link:
                    continue
                descricao = item.findtext("description", "")
                soup = BeautifulSoup(descricao, "html.parser")
                img = soup.find("img")
                imagem = img["src"] if img and img.get("src") else None
                ofertas.append(Oferta(titulo=titulo, preco="Ver site", link=link,
                                      fonte="Pelando", imagem=imagem))
        log.info(f"Pelando RSS: {len(ofertas)} ofertas")
    except Exception as e:
        log.warning(f"Pelando RSS erro: {e}")
    return ofertas


async def buscar_promobit_rss(client):
    ofertas = []
    try:
        r = await client.get("https://www.promobit.com.br/feed/offers.rss", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:30]:
                titulo = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                if not titulo or not link:
                    continue
                descricao = item.findtext("description", "")
                soup = BeautifulSoup(descricao, "html.parser")
                img = soup.find("img")
                imagem = img["src"] if img and img.get("src") else None
                ofertas.append(Oferta(titulo=titulo, preco="Ver site", link=link,
                                      fonte="Promobit", imagem=imagem))
        log.info(f"Promobit RSS: {len(ofertas)} ofertas")
    except Exception as e:
        log.warning(f"Promobit RSS erro: {e}")
    return ofertas


async def buscar_kabum(client):
    ofertas = []
    try:
        r = await client.get("https://www.kabum.com.br/ofertas?sort=mais_vendidos",
                             headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("article, [class*='Card'], [class*='product']")[:20]
        for card in cards:
            titulo_el = card.select_one("[class*='name'], [class*='title'], h2, h3")
            preco_el = card.select_one("[class*='price'], [class*='Price']")
            link_el = card.select_one("a[href]")
            img_el = card.select_one("img")
            if not titulo_el or not link_el:
                continue
            titulo = titulo_el.get_text(strip=True)
            preco = preco_el.get_text(strip=True) if preco_el else "Ver site"
            href = link_el["href"]
            link = href if href.startswith("http") else f"https://www.kabum.com.br{href}"
            imagem = img_el.get("src") if img_el else None
            if titulo and len(titulo) > 5:
                ofertas.append(Oferta(titulo=titulo, preco=preco, link=link,
                                      fonte="KaBuM!", imagem=imagem))
        log.info(f"KaBuM!: {len(ofertas)} ofertas")
    except Exception as e:
        log.warning(f"KaBuM! erro: {e}")
    return ofertas


async def buscar_shopee(client):
    ofertas = []
    try:
        r = await client.get("https://shopee.com.br/m/flash-sale", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("[class*='item'], [class*='product']")[:20]
        for card in cards:
            titulo_el = card.select_one("[class*='name'], [class*='title']")
            preco_el = card.select_one("[class*='price']")
            link_el = card.select_one("a[href]")
            if not titulo_el or not link_el:
                continue
            titulo = titulo_el.get_text(strip=True)
            preco = preco_el.get_text(strip=True) if preco_el else "Ver site"
            href = link_el["href"]
            link = href if href.startswith("http") else f"https://shopee.com.br{href}"
            if titulo and len(titulo) > 5:
                ofertas.append(Oferta(titulo=titulo, preco=preco, link=link, fonte="Shopee"))
        log.info(f"Shopee: {len(ofertas)} ofertas")
    except Exception as e:
        log.warning(f"Shopee erro: {e}")
    return ofertas


def formatar_mensagem(oferta: Oferta) -> str:
    emoji = {
        "Pelando": "🔥", "Promobit": "⚡",
        "KaBuM!": "💥", "Shopee": "🧡"
    }.get(oferta.fonte, "💰")
    return (
        f"{emoji} <b>{oferta.titulo}</b>\n\n"
        f"💰 <b>Preço:</b> {oferta.preco}\n"
        f"🏪 <b>Fonte:</b> {oferta.fonte}\n"
        f"🕐 {datetime.now().strftime('%d/%m %H:%M')}\n\n"
        f"👉 <a href='{oferta.link}'>Ver oferta</a>"
    )


async def enviar(bot: Bot, oferta: Oferta):
    msg = formatar_mensagem(oferta)
    try:
        if oferta.imagem and oferta.imagem.startswith("http"):
            await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=oferta.imagem,
                                 caption=msg, parse_mode=ParseMode.HTML)
        else:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg,
                                   parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning(f"Erro ao enviar: {e}")
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg,
                                   parse_mode=ParseMode.HTML)
        except Exception as e2:
            log.error(f"Falha total: {e2}")


async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    vistas = carregar_vistas()

    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text="🤖 <b>Bot reiniciado!</b>\n\n"
             "Monitorando: Pelando, Promobit, KaBuM! e Shopee\n"
             "⏱️ Verificando a cada 60 segundos",
        parse_mode=ParseMode.HTML
    )

    while True:
        log.info("Verificando ofertas...")
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resultados = await asyncio.gather(
                buscar_pelando_rss(client),
                buscar_promobit_rss(client),
                buscar_kabum(client),
                buscar_shopee(client),
                return_exceptions=True
            )

        novas = 0
        for grupo in resultados:
            if isinstance(grupo, Exception):
                continue
            for oferta in grupo:
                if oferta.id() not in vistas:
                    vistas.add(oferta.id())
                    await enviar(bot, oferta)
                    novas += 1
                    await asyncio.sleep(2)

        salvar_vistas(vistas)
        log.info(f"✅ {novas} nova(s) oferta(s) enviada(s)")
        await asyncio.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    asyncio.run(main())
