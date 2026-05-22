import asyncio
import logging
import hashlib
import json
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode

# =============================================
# CONFIGURAÇÕES — edite aqui
# =============================================
TELEGRAM_TOKEN = "8928368941:AAG8FAM49Wj71HixaMyaoFK1qXGQN8FvLEo"
TELEGRAM_CHAT_ID = "656910452"
INTERVALO_MINUTOS = 1
CATEGORIAS = ["eletrônicos", "games", "informática", "notebook",
               "smartphone", "console", "placa de vídeo", "monitor",
               "teclado", "mouse", "headset", "processador", "ssd",
               "tablet", "fone", "câmera", "impressora", "roteador",
               "gpu", "cpu", "memória", "fonte", "gabinete", "cooler"]
# =============================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)
VISTAS_FILE = "ofertas_vistas.json"
CUPONS_VISTOS_FILE = "cupons_vistos.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def carregar_vistas() -> set:
    if os.path.exists(VISTAS_FILE):
        with open(VISTAS_FILE) as f:
            return set(json.load(f))
    return set()


def salvar_vistas(vistas: set):
    with open(VISTAS_FILE, "w") as f:
        json.dump(list(vistas), f)


def carregar_cupons_vistos() -> set:
    if os.path.exists(CUPONS_VISTOS_FILE):
        with open(CUPONS_VISTOS_FILE) as f:
            return set(json.load(f))
    return set()


def salvar_cupons_vistos(vistos: set):
    with open(CUPONS_VISTOS_FILE, "w") as f:
        json.dump(list(vistos), f)


@dataclass
class Oferta:
    titulo: str
    preco: str
    link: str
    fonte: str
    imagem: Optional[str] = None

    def id(self) -> str:
        return hashlib.md5(self.link.encode()).hexdigest()


@dataclass
class Cupom:
    loja: str
    codigo: str
    descricao: str
    link: str
    fonte: str

    def id(self) -> str:
        return hashlib.md5((self.loja + self.codigo).encode()).hexdigest()


def eh_relevante(titulo: str) -> bool:
    t = titulo.lower()
    return any(cat in t for cat in CATEGORIAS)


# ─── OFERTAS ──────────────────────────────────────────────────────────────────

async def buscar_pelando(client):
    ofertas = []
    try:
        r = await client.get("https://www.pelando.com.br/", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select("article")[:30]:
            titulo_el = card.select_one("h3, h2, [class*='title']")
            preco_el = card.select_one("[class*='price']")
            link_el = card.select_one("a[href]")
            img_el = card.select_one("img")
            if not titulo_el or not link_el: continue
            titulo = titulo_el.get_text(strip=True)
            preco = preco_el.get_text(strip=True) if preco_el else "Ver site"
            href = link_el["href"]
            link = href if href.startswith("http") else f"https://www.pelando.com.br{href}"
            imagem = img_el.get("src") if img_el else None
            if eh_relevante(titulo):
                ofertas.append(Oferta(titulo=titulo, preco=preco, link=link, fonte="Pelando", imagem=imagem))
    except Exception as e:
        log.warning(f"Pelando erro: {e}")
    return ofertas


async def buscar_promobit(client):
    ofertas = []
    try:
        r = await client.get("https://www.promobit.com.br/", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select("article, [class*='offer']")[:30]:
            titulo_el = card.select_one("h2, h3, [class*='title']")
            preco_el = card.select_one("[class*='price']")
            link_el = card.select_one("a[href]")
            img_el = card.select_one("img")
            if not titulo_el or not link_el: continue
            titulo = titulo_el.get_text(strip=True)
            preco = preco_el.get_text(strip=True) if preco_el else "Ver site"
            href = link_el["href"]
            link = href if href.startswith("http") else f"https://www.promobit.com.br{href}"
            imagem = img_el.get("src") if img_el else None
            if eh_relevante(titulo):
                ofertas.append(Oferta(titulo=titulo, preco=preco, link=link, fonte="Promobit", imagem=imagem))
    except Exception as e:
        log.warning(f"Promobit erro: {e}")
    return ofertas


async def buscar_zoom(client):
    ofertas = []
    try:
        for cat in ["eletronicos", "games", "informatica"]:
            r = await client.get(f"https://www.zoom.com.br/mais-vendidos/{cat}", headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select("[class*='product'], article")[:10]:
                titulo_el = card.select_one("h2, h3, [class*='title']")
                preco_el = card.select_one("[class*='price']")
                link_el = card.select_one("a[href]")
                if not titulo_el or not link_el: continue
                titulo = titulo_el.get_text(strip=True)
                preco = preco_el.get_text(strip=True) if preco_el else "Ver site"
                href = link_el["href"]
                link = href if href.startswith("http") else f"https://www.zoom.com.br{href}"
                ofertas.append(Oferta(titulo=titulo, preco=preco, link=link, fonte="Zoom"))
    except Exception as e:
        log.warning(f"Zoom erro: {e}")
    return ofertas


async def buscar_mercadolivre(client):
    ofertas = []
    try:
        for termo in ["notebook", "smartphone", "games"]:
            r = await client.get(f"https://www.mercadolivre.com.br/{termo}", headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select(".ui-search-result__wrapper")[:8]:
                titulo_el = card.select_one("h2, [class*='title']")
                preco_el = card.select_one("[class*='price__fraction']")
                link_el = card.select_one("a[href]")
                if not titulo_el or not link_el: continue
                titulo = titulo_el.get_text(strip=True)
                preco = "R$ " + preco_el.get_text(strip=True) if preco_el else "Ver site"
                if eh_relevante(titulo):
                    ofertas.append(Oferta(titulo=titulo, preco=preco, link=link_el["href"], fonte="Mercado Livre"))
    except Exception as e:
        log.warning(f"Mercado Livre erro: {e}")
    return ofertas


async def buscar_amazon(client):
    ofertas = []
    try:
        for url in ["https://www.amazon.com.br/gp/bestsellers/electronics",
                    "https://www.amazon.com.br/gp/bestsellers/computers",
                    "https://www.amazon.com.br/gp/bestsellers/videogames"]:
            r = await client.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select("[class*='zg-item'], [data-asin]")[:8]:
                titulo_el = card.select_one("[class*='p13n-sc-truncated'], a")
                preco_el = card.select_one("[class*='p13n-sc-price']")
                link_el = card.select_one("a[href]")
                if not titulo_el or not link_el: continue
                titulo = titulo_el.get_text(strip=True)
                preco = preco_el.get_text(strip=True) if preco_el else "Ver site"
                href = link_el["href"]
                link = href if href.startswith("http") else f"https://www.amazon.com.br{href}"
                if titulo and len(titulo) > 5:
                    ofertas.append(Oferta(titulo=titulo, preco=preco, link=link, fonte="Amazon"))
    except Exception as e:
        log.warning(f"Amazon erro: {e}")
    return ofertas


async def buscar_shopee(client):
    ofertas = []
    try:
        for cat in ["electronics", "computer-peripherals", "mobile-gadgets"]:
            r = await client.get(f"https://shopee.com.br/search?keyword={cat}&sortBy=sales", headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select("[class*='shopee-search-item']")[:8]:
                titulo_el = card.select_one("[class*='name']")
                preco_el = card.select_one("[class*='price']")
                link_el = card.select_one("a[href]")
                if not titulo_el or not link_el: continue
                titulo = titulo_el.get_text(strip=True)
                preco = preco_el.get_text(strip=True) if preco_el else "Ver site"
                href = link_el["href"]
                link = href if href.startswith("http") else f"https://shopee.com.br{href}"
                if eh_relevante(titulo):
                    ofertas.append(Oferta(titulo=titulo, preco=preco, link=link, fonte="Shopee"))
    except Exception as e:
        log.warning(f"Shopee erro: {e}")
    return ofertas


async def buscar_aliexpress(client):
    ofertas = []
    try:
        for termo in ["electronics", "gaming", "laptop", "smartphone"]:
            r = await client.get(f"https://www.aliexpress.com/wholesale?SearchText={termo}&SortType=total_tranpro_desc", headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select("[class*='product-card']")[:8]:
                titulo_el = card.select_one("[class*='title']")
                preco_el = card.select_one("[class*='price']")
                link_el = card.select_one("a[href]")
                if not titulo_el or not link_el: continue
                titulo = titulo_el.get_text(strip=True)
                preco = preco_el.get_text(strip=True) if preco_el else "Ver site"
                href = link_el["href"]
                link = href if href.startswith("http") else f"https://www.aliexpress.com{href}"
                if titulo and len(titulo) > 5:
                    ofertas.append(Oferta(titulo=titulo, preco=preco, link=link, fonte="AliExpress"))
    except Exception as e:
        log.warning(f"AliExpress erro: {e}")
    return ofertas


async def buscar_kabum(client):
    ofertas = []
    try:
        for cat in ["hardware", "games", "celular-smartphone", "notebook-e-netbook"]:
            r = await client.get(f"https://www.kabum.com.br/{cat}?sort=mais_vendidos", headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select("[class*='productCard'], article")[:10]:
                titulo_el = card.select_one("span[class*='nameCard'], h2, h3, [class*='title']")
                preco_el = card.select_one("[class*='priceCard'], [class*='price']")
                link_el = card.select_one("a[href]")
                img_el = card.select_one("img")
                if not titulo_el or not link_el: continue
                titulo = titulo_el.get_text(strip=True)
                preco = preco_el.get_text(strip=True) if preco_el else "Ver site"
                href = link_el["href"]
                link = href if href.startswith("http") else f"https://www.kabum.com.br{href}"
                imagem = img_el.get("src") if img_el else None
                if titulo and len(titulo) > 5:
                    ofertas.append(Oferta(titulo=titulo, preco=preco, link=link, fonte="KaBuM!", imagem=imagem))
    except Exception as e:
        log.warning(f"KaBuM! erro: {e}")
    return ofertas


async def buscar_pichau(client):
    ofertas = []
    try:
        for cat in ["placas-de-video", "processadores", "memoria-ram", "notebooks", "monitores"]:
            r = await client.get(f"https://www.pichau.com.br/{cat}?sort=price-desc", headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select("[class*='MuiCard'], article")[:10]:
                titulo_el = card.select_one("h2, h3, [class*='title']")
                preco_el = card.select_one("[class*='price']")
                link_el = card.select_one("a[href]")
                if not titulo_el or not link_el: continue
                titulo = titulo_el.get_text(strip=True)
                preco = preco_el.get_text(strip=True) if preco_el else "Ver site"
                href = link_el["href"]
                link = href if href.startswith("http") else f"https://www.pichau.com.br{href}"
                if titulo and len(titulo) > 5:
                    ofertas.append(Oferta(titulo=titulo, preco=preco, link=link, fonte="Pichau"))
    except Exception as e:
        log.warning(f"Pichau erro: {e}")
    return ofertas


async def buscar_terabyte(client):
    ofertas = []
    try:
        for cat in ["placas-de-video", "processadores", "memoria", "notebook", "monitor"]:
            r = await client.get(f"https://www.terabyteshop.com.br/hardware/{cat}", headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select("[class*='product'], [class*='pbox']")[:10]:
                titulo_el = card.select_one("h2, h3, [class*='title'], [class*='prod-name']")
                preco_el = card.select_one("[class*='price'], [class*='prod-new-price']")
                link_el = card.select_one("a[href]")
                if not titulo_el or not link_el: continue
                titulo = titulo_el.get_text(strip=True)
                preco = preco_el.get_text(strip=True) if preco_el else "Ver site"
                href = link_el["href"]
                link = href if href.startswith("http") else f"https://www.terabyteshop.com.br{href}"
                if titulo and len(titulo) > 5:
                    ofertas.append(Oferta(titulo=titulo, preco=preco, link=link, fonte="Terabyte"))
    except Exception as e:
        log.warning(f"Terabyte erro: {e}")
    return ofertas


# ─── CUPONS ───────────────────────────────────────────────────────────────────

async def buscar_cupons_pelando(client):
    cupons = []
    try:
        r = await client.get("https://www.pelando.com.br/cupons", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select("article, [class*='coupon']")[:20]:
            loja_el = card.select_one("[class*='store'], h2, h3")
            codigo_el = card.select_one("[class*='code'], code")
            desc_el = card.select_one("[class*='desc'], [class*='title'], p")
            link_el = card.select_one("a[href]")
            if not loja_el or not link_el: continue
            loja = loja_el.get_text(strip=True)
            codigo = codigo_el.get_text(strip=True) if codigo_el else "Ver site"
            descricao = desc_el.get_text(strip=True) if desc_el else "Cupom disponível"
            href = link_el["href"]
            link = href if href.startswith("http") else f"https://www.pelando.com.br{href}"
            cupons.append(Cupom(loja=loja, codigo=codigo, descricao=descricao, link=link, fonte="Pelando"))
    except Exception as e:
        log.warning(f"Cupons Pelando erro: {e}")
    return cupons


async def buscar_cupons_promobit(client):
    cupons = []
    try:
        r = await client.get("https://www.promobit.com.br/cupons", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select("[class*='coupon'], article")[:20]:
            loja_el = card.select_one("[class*='store'], [class*='brand'], h2, h3")
            codigo_el = card.select_one("[class*='code'], code")
            desc_el = card.select_one("[class*='desc'], [class*='title'], p")
            link_el = card.select_one("a[href]")
            if not loja_el or not link_el: continue
            loja = loja_el.get_text(strip=True)
            codigo = codigo_el.get_text(strip=True) if codigo_el else "Ver site"
            descricao = desc_el.get_text(strip=True) if desc_el else "Cupom disponível"
            href = link_el["href"]
            link = href if href.startswith("http") else f"https://www.promobit.com.br{href}"
            cupons.append(Cupom(loja=loja, codigo=codigo, descricao=descricao, link=link, fonte="Promobit"))
    except Exception as e:
        log.warning(f"Cupons Promobit erro: {e}")
    return cupons


async def buscar_cupons_meliuz(client):
    cupons = []
    try:
        r = await client.get("https://www.meliuz.com.br/cupons", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select("[class*='coupon'], [class*='offer'], article")[:20]:
            loja_el = card.select_one("[class*='store'], [class*='brand'], h2, h3")
            codigo_el = card.select_one("[class*='code'], [class*='codigo']")
            desc_el = card.select_one("[class*='desc'], [class*='title'], p")
            link_el = card.select_one("a[href]")
            if not loja_el or not link_el: continue
            loja = loja_el.get_text(strip=True)
            codigo = codigo_el.get_text(strip=True) if codigo_el else "Ver site"
            descricao = desc_el.get_text(strip=True) if desc_el else "Cupom disponível"
            href = link_el["href"]
            link = href if href.startswith("http") else f"https://www.meliuz.com.br{href}"
            cupons.append(Cupom(loja=loja, codigo=codigo, descricao=descricao, link=link, fonte="Méliuz"))
    except Exception as e:
        log.warning(f"Cupons Méliuz erro: {e}")
    return cupons


async def buscar_cupons_kabum(client):
    cupons = []
    try:
        r = await client.get("https://www.kabum.com.br/cupom-de-desconto", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select("[class*='coupon'], [class*='cupom'], article")[:20]:
            loja_el = card.select_one("[class*='store'], [class*='title'], h2, h3")
            codigo_el = card.select_one("[class*='code'], [class*='codigo'], code")
            desc_el = card.select_one("[class*='desc'], p")
            link_el = card.select_one("a[href]")
            if not link_el: continue
            loja = loja_el.get_text(strip=True) if loja_el else "KaBuM!"
            codigo = codigo_el.get_text(strip=True) if codigo_el else "Ver site"
            descricao = desc_el.get_text(strip=True) if desc_el else "Cupom KaBuM!"
            href = link_el["href"]
            link = href if href.startswith("http") else f"https://www.kabum.com.br{href}"
            cupons.append(Cupom(loja=loja, codigo=codigo, descricao=descricao, link=link, fonte="KaBuM!"))
    except Exception as e:
        log.warning(f"Cupons KaBuM! erro: {e}")
    return cupons


async def buscar_cupons_pichau(client):
    cupons = []
    try:
        r = await client.get("https://www.pichau.com.br/cupom-de-desconto", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select("[class*='coupon'], [class*='cupom'], article")[:20]:
            loja_el = card.select_one("[class*='title'], h2, h3")
            codigo_el = card.select_one("[class*='code'], code")
            desc_el = card.select_one("[class*='desc'], p")
            link_el = card.select_one("a[href]")
            if not link_el: continue
            loja = loja_el.get_text(strip=True) if loja_el else "Pichau"
            codigo = codigo_el.get_text(strip=True) if codigo_el else "Ver site"
            descricao = desc_el.get_text(strip=True) if desc_el else "Cupom Pichau"
            href = link_el["href"]
            link = href if href.startswith("http") else f"https://www.pichau.com.br{href}"
            cupons.append(Cupom(loja=loja, codigo=codigo, descricao=descricao, link=link, fonte="Pichau"))
    except Exception as e:
        log.warning(f"Cupons Pichau erro: {e}")
    return cupons


async def buscar_cupons_terabyte(client):
    cupons = []
    try:
        r = await client.get("https://www.terabyteshop.com.br/cupons", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select("[class*='coupon'], [class*='cupom'], article")[:20]:
            loja_el = card.select_one("[class*='title'], h2, h3")
            codigo_el = card.select_one("[class*='code'], code")
            desc_el = card.select_one("[class*='desc'], p")
            link_el = card.select_one("a[href]")
            if not link_el: continue
            loja = loja_el.get_text(strip=True) if loja_el else "Terabyte"
            codigo = codigo_el.get_text(strip=True) if codigo_el else "Ver site"
            descricao = desc_el.get_text(strip=True) if desc_el else "Cupom Terabyte"
            href = link_el["href"]
            link = href if href.startswith("http") else f"https://www.terabyteshop.com.br{href}"
            cupons.append(Cupom(loja=loja, codigo=codigo, descricao=descricao, link=link, fonte="Terabyte"))
    except Exception as e:
        log.warning(f"Cupons Terabyte erro: {e}")
    return cupons


async def buscar_cupons_shopee(client):
    cupons = []
    try:
        r = await client.get("https://shopee.com.br/m/voucher-code", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select("[class*='voucher'], [class*='coupon'], article")[:20]:
            loja_el = card.select_one("[class*='title'], h2, h3")
            codigo_el = card.select_one("[class*='code'], code")
            desc_el = card.select_one("[class*='desc'], p")
            link_el = card.select_one("a[href]")
            if not link_el: continue
            loja = loja_el.get_text(strip=True) if loja_el else "Shopee"
            codigo = codigo_el.get_text(strip=True) if codigo_el else "Ver site"
            descricao = desc_el.get_text(strip=True) if desc_el else "Cupom Shopee"
            href = link_el["href"]
            link = href if href.startswith("http") else f"https://shopee.com.br{href}"
            cupons.append(Cupom(loja=loja, codigo=codigo, descricao=descricao, link=link, fonte="Shopee"))
    except Exception as e:
        log.warning(f"Cupons Shopee erro: {e}")
    return cupons


async def buscar_cupons_aliexpress(client):
    cupons = []
    try:
        r = await client.get("https://www.aliexpress.com/coupon/coupons.html", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select("[class*='coupon'], [class*='voucher']")[:20]:
            loja_el = card.select_one("[class*='title'], h2, h3")
            codigo_el = card.select_one("[class*='code'], code")
            desc_el = card.select_one("[class*='desc'], p")
            link_el = card.select_one("a[href]")
            if not link_el: continue
            loja = loja_el.get_text(strip=True) if loja_el else "AliExpress"
            codigo = codigo_el.get_text(strip=True) if codigo_el else "Ver site"
            descricao = desc_el.get_text(strip=True) if desc_el else "Cupom AliExpress"
            href = link_el["href"]
            link = href if href.startswith("http") else f"https://www.aliexpress.com{href}"
            cupons.append(Cupom(loja=loja, codigo=codigo, descricao=descricao, link=link, fonte="AliExpress"))
    except Exception as e:
        log.warning(f"Cupons AliExpress erro: {e}")
    return cupons


async def buscar_cupons_amazon(client):
    cupons = []
    try:
        r = await client.get("https://www.amazon.com.br/coupons", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select("[class*='coupon'], [data-asin]")[:20]:
            loja_el = card.select_one("[class*='title'], h2, h3, a")
            codigo_el = card.select_one("[class*='code'], [class*='discount']")
            desc_el = card.select_one("[class*='desc'], p")
            link_el = card.select_one("a[href]")
            if not link_el: continue
            loja = loja_el.get_text(strip=True) if loja_el else "Amazon"
            codigo = codigo_el.get_text(strip=True) if codigo_el else "Ver site"
            descricao = desc_el.get_text(strip=True) if desc_el else "Cupom Amazon"
            href = link_el["href"]
            link = href if href.startswith("http") else f"https://www.amazon.com.br{href}"
            cupons.append(Cupom(loja=loja, codigo=codigo, descricao=descricao, link=link, fonte="Amazon"))
    except Exception as e:
        log.warning(f"Cupons Amazon erro: {e}")
    return cupons


async def buscar_cupons_mercadolivre(client):
    cupons = []
    try:
        r = await client.get("https://www.mercadolivre.com.br/cupons-de-desconto", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select("[class*='coupon'], [class*='cupom'], article")[:20]:
            loja_el = card.select_one("[class*='store'], [class*='title'], h2, h3")
            codigo_el = card.select_one("[class*='code'], [class*='codigo']")
            desc_el = card.select_one("[class*='desc'], p")
            link_el = card.select_one("a[href]")
            if not link_el: continue
            loja = loja_el.get_text(strip=True) if loja_el else "Mercado Livre"
            codigo = codigo_el.get_text(strip=True) if codigo_el else "Ver site"
            descricao = desc_el.get_text(strip=True) if desc_el else "Cupom Mercado Livre"
            href = link_el["href"]
            link = href if href.startswith("http") else f"https://www.mercadolivre.com.br{href}"
            cupons.append(Cupom(loja=loja, codigo=codigo, descricao=descricao, link=link, fonte="Mercado Livre"))
    except Exception as e:
        log.warning(f"Cupons Mercado Livre erro: {e}")
    return cupons


# ─── FORMATAR E ENVIAR ────────────────────────────────────────────────────────

def formatar_oferta(oferta: Oferta) -> str:
    emoji = {
        "Pelando": "🔥", "Promobit": "⚡", "Zoom": "🔍",
        "Mercado Livre": "🛒", "Amazon": "📦", "Shopee": "🧡",
        "AliExpress": "🌏", "KaBuM!": "💥", "Pichau": "🖥️", "Terabyte": "💾"
    }.get(oferta.fonte, "💰")
    return (
        f"{emoji} <b>{oferta.titulo}</b>\n\n"
        f"💰 <b>Preço:</b> {oferta.preco}\n"
        f"🏪 <b>Fonte:</b> {oferta.fonte}\n"
        f"🕐 <b>Encontrado:</b> {datetime.now().strftime('%d/%m %H:%M')}\n\n"
        f"👉 <a href='{oferta.link}'>Ver oferta</a>"
    )


def formatar_cupom(cupom: Cupom) -> str:
    return (
        f"🎟️ <b>CUPOM — {cupom.loja}</b>\n\n"
        f"📝 <b>Descrição:</b> {cupom.descricao}\n"
        f"🔑 <b>Código:</b> <code>{cupom.codigo}</code>\n"
        f"🏪 <b>Fonte:</b> {cupom.fonte}\n"
        f"🕐 <b>Encontrado:</b> {datetime.now().strftime('%d/%m %H:%M')}\n\n"
        f"👉 <a href='{cupom.link}'>Ver cupom</a>"
    )


async def enviar_oferta(bot: Bot, oferta: Oferta):
    msg = formatar_oferta(oferta)
    try:
        if oferta.imagem and oferta.imagem.startswith("http"):
            await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=oferta.imagem,
                                 caption=msg, parse_mode=ParseMode.HTML)
        else:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg,
                                   parse_mode=ParseMode.HTML, disable_web_page_preview=False)
    except Exception as e:
        log.warning(f"Erro ao enviar oferta: {e}")
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode=ParseMode.HTML)
        except Exception as e2:
            log.error(f"Falha total: {e2}")


async def enviar_cupom(bot: Bot, cupom: Cupom):
    msg = formatar_cupom(cupom)
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg,
                               parse_mode=ParseMode.HTML, disable_web_page_preview=False)
    except Exception as e:
        log.warning(f"Erro ao enviar cupom: {e}")


# ─── LOOP PRINCIPAL ───────────────────────────────────────────────────────────

async def verificar_ofertas(bot: Bot, vistas: set):
    log.info("Verificando ofertas...")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resultados = await asyncio.gather(
            buscar_pelando(client), buscar_promobit(client), buscar_zoom(client),
            buscar_mercadolivre(client), buscar_amazon(client), buscar_shopee(client),
            buscar_aliexpress(client), buscar_kabum(client), buscar_pichau(client),
            buscar_terabyte(client),
            return_exceptions=True
        )
    novas = 0
    for grupo in resultados:
        if isinstance(grupo, Exception): continue
        for oferta in grupo:
            if oferta.id() not in vistas:
                vistas.add(oferta.id())
                await enviar_oferta(bot, oferta)
                novas += 1
                await asyncio.sleep(1)
    salvar_vistas(vistas)
    log.info(f"✅ {novas} nova(s) oferta(s) enviada(s)")


async def verificar_cupons(bot: Bot, cupons_vistos: set):
    log.info("Verificando cupons...")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resultados = await asyncio.gather(
            buscar_cupons_pelando(client), buscar_cupons_promobit(client),
            buscar_cupons_meliuz(client), buscar_cupons_kabum(client),
            buscar_cupons_pichau(client), buscar_cupons_terabyte(client),
            buscar_cupons_shopee(client), buscar_cupons_aliexpress(client),
            buscar_cupons_amazon(client), buscar_cupons_mercadolivre(client),
            return_exceptions=True
        )
    novos = 0
    for grupo in resultados:
        if isinstance(grupo, Exception): continue
        for cupom in grupo:
            if cupom.id() not in cupons_vistos:
                cupons_vistos.add(cupom.id())
                await enviar_cupom(bot, cupom)
                novos += 1
                await asyncio.sleep(1)
    salvar_cupons_vistos(cupons_vistos)
    log.info(f"🎟️ {novos} novo(s) cupom(ns) enviado(s)")


async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    vistas = carregar_vistas()
    cupons_vistos = carregar_cupons_vistos()

    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text="🤖 <b>Bot de Ofertas + Cupons iniciado!</b>\n\n"
             "🛍️ <b>Ofertas:</b> Pelando, Promobit, Zoom, Mercado Livre, Amazon, Shopee, AliExpress, KaBuM!, Pichau e Terabyte\n\n"
             "🎟️ <b>Cupons:</b> Pelando, Promobit, Méliuz, KaBuM!, Pichau, Terabyte, Shopee, AliExpress, Amazon e Mercado Livre\n\n"
             "📦 Categorias: Eletrônicos, Games e Informática",
        parse_mode=ParseMode.HTML
    )

    while True:
        await verificar_ofertas(bot, vistas)
        await verificar_cupons(bot, cupons_vistos)
        log.info(f"Aguardando {INTERVALO_MINUTOS} minutos...")
        await asyncio.sleep(INTERVALO_MINUTOS * 60)


if __name__ == "__main__":
    asyncio.run(main())
