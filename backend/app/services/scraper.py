import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

import requests
from playwright.async_api import async_playwright

from app.services.exchange import get_aud_to_lkr_rate
from app.services.pricing import calculate_lkr_price, choose_reference_price


@dataclass
class ScrapedProduct:
    source_url: str
    name: str
    price_aud: float
    msrp_aud: float | None = None
    rrp_aud: float | None = None
    image_url: str | None = None
    sku: str | None = None
    description: str | None = None


@dataclass
class ProductTarget:
    source_url: str
    lastmod: datetime | None = None


ProgressCallback = Callable[[int, int, str, str], None]

SITEMAP_NAMESPACE = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
PRODUCT_EXCLUDE_PREFIXES = (
    "/catalog/category/",
    "/stores/",
    "/tips-tricks-tech/",
    "/specials/",
    "/media/",
)


def discover_product_urls(seeds: Iterable[str]) -> list[str]:
    return [target.source_url for target in discover_product_targets(seeds)]


def discover_product_targets(seeds: Iterable[str]) -> list[ProductTarget]:
    discovered: dict[str, datetime | None] = {}
    for seed in seeds:
        seed = seed.strip()
        if not seed:
            continue
        if seed.endswith(".xml"):
            for target in _extract_product_targets_from_sitemap(seed):
                current_lastmod = discovered.get(target.source_url)
                discovered[target.source_url] = _latest_lastmod(current_lastmod, target.lastmod)
            continue
        for url in _extract_product_urls_from_page(seed):
            discovered.setdefault(url, None)
    return [ProductTarget(source_url=url, lastmod=discovered[url]) for url in sorted(discovered)]


def scrape_product_urls(
    urls: Iterable[str],
    progress_callback: ProgressCallback | None = None,
) -> list[ScrapedProduct]:
    results: list[ScrapedProduct] = []
    url_list = list(urls)
    async def _scrape() -> None:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            total = len(url_list)
            for index, url in enumerate(url_list, start=1):
                if progress_callback:
                    progress_callback(index - 1, total, "scraping", f"Opening {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                result = await _extract_product_from_page(page, url)
                results.append(result)
                if progress_callback:
                    progress_callback(index, total, "scraping", f"Scraped {index} of {total} URLs")
            await browser.close()

    asyncio.run(_scrape())
    return results


def build_pricing_payload(product: ScrapedProduct, handling_fee_percent: float) -> dict[str, float | str | None]:
    exchange_rate = get_aud_to_lkr_rate()
    base_price = choose_reference_price(product.msrp_aud, product.rrp_aud, product.price_aud)
    return {
        "source_url": product.source_url,
        "name": product.name,
        "price_aud": base_price,
        "msrp_aud": product.msrp_aud,
        "rrp_aud": product.rrp_aud,
        "price_lkr": calculate_lkr_price(base_price, exchange_rate, handling_fee_percent),
        "exchange_rate_aud_lkr": exchange_rate,
        "image_url": product.image_url,
        "sku": product.sku,
        "description": product.description,
    }


def _extract_price_from_text(text: str) -> float:
    import re

    match = re.search(r"\$([0-9]+(?:\.[0-9]{1,2})?)", text)
    if match:
        return float(match.group(1))
    return 0.0


def run_scrape(urls: Iterable[str], progress_callback: ProgressCallback | None = None) -> list[ScrapedProduct]:
    return scrape_product_urls(urls, progress_callback=progress_callback)


def _extract_product_targets_from_sitemap(sitemap_url: str) -> list[ProductTarget]:
    response = requests.get(sitemap_url, timeout=30)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    targets: list[ProductTarget] = []
    if root.tag.endswith("sitemapindex"):
        for loc in root.findall("sm:sitemap/sm:loc", SITEMAP_NAMESPACE):
            targets.extend(_extract_product_targets_from_sitemap(loc.text or ""))
        return targets

    for url_node in root.findall("sm:url", SITEMAP_NAMESPACE):
        loc = url_node.find("sm:loc", SITEMAP_NAMESPACE)
        if loc is None:
            continue
        url = (loc.text or "").strip()
        if _is_product_url(url):
            lastmod_node = url_node.find("sm:lastmod", SITEMAP_NAMESPACE)
            lastmod = _parse_sitemap_lastmod((lastmod_node.text or "").strip()) if lastmod_node is not None else None
            targets.append(ProductTarget(source_url=url, lastmod=lastmod))
    return targets


def _extract_product_urls_from_page(page_url: str) -> list[str]:
    response = requests.get(page_url, timeout=30)
    response.raise_for_status()
    matches = set()
    for candidate in _href_candidates(response.text):
        if _is_product_url(candidate):
            matches.add(urljoin(page_url, candidate))
    return sorted(matches)


def _href_candidates(html: str) -> list[str]:
    import re

    return re.findall(r'href=["\\\']([^"\\\']+\\.html[^"\\\']*)["\\\']', html)


def _is_product_url(url: str) -> bool:
    if not url or not url.startswith("http"):
        return False
    path = url.split("https://www.4wdsupacentre.com.au", 1)[-1]
    if any(path.startswith(prefix) for prefix in PRODUCT_EXCLUDE_PREFIXES):
        return False
    return path.endswith(".html")


async def _extract_product_from_page(page, url: str) -> ScrapedProduct:
    title = await page.title()
    description = await _meta_content(page, 'meta[name="description"]')
    image_url = await _meta_content(page, 'meta[property="og:image"]')
    sku = None
    name = title or url
    price = 0.0
    msrp = None
    rrp = None

    ld_json_values = await page.locator('script[type="application/ld+json"]').all_text_contents()
    for raw in ld_json_values:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for item in _iter_json_objects(data):
            if not isinstance(item, dict):
                continue
            types = item.get("@type")
            if isinstance(types, str):
                types = [types]
            if not types or "Product" not in types:
                continue
            name = item.get("name") or name
            sku = item.get("sku") or sku
            image = item.get("image")
            if isinstance(image, list):
                image = image[0] if image else None
            if image and not image_url:
                image_url = image
            desc = item.get("description")
            if desc and not description:
                description = str(desc)
            offers = item.get("offers")
            if isinstance(offers, dict):
                price = _coerce_price(offers.get("price")) or price
            aggregate = item.get("aggregateOffer")
            if isinstance(aggregate, dict):
                msrp = _coerce_price(aggregate.get("lowPrice")) or msrp
                rrp = _coerce_price(aggregate.get("highPrice")) or rrp
            break

    if not price:
        text = await page.locator("body").inner_text()
        price = _extract_price_from_text(text)
        if not description:
            description = text[:500]

    return ScrapedProduct(
        source_url=url,
        name=str(name),
        price_aud=price,
        msrp_aud=msrp,
        rrp_aud=rrp,
        image_url=image_url,
        sku=sku,
        description=description,
    )


async def _meta_content(page, selector: str) -> str | None:
    locator = page.locator(selector)
    if await locator.count():
        value = await locator.first.get_attribute("content")
        return value or None
    return None


def _iter_json_objects(data):
    if isinstance(data, list):
        for item in data:
            yield from _iter_json_objects(item)
    elif isinstance(data, dict):
        yield data
        for value in data.values():
            yield from _iter_json_objects(value)


def _coerce_price(value) -> float | None:
    try:
        if value is None:
            return None
        price = float(value)
        return price if price > 0 else None
    except (TypeError, ValueError):
        return None


def _parse_sitemap_lastmod(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _latest_lastmod(current: datetime | None, candidate: datetime | None) -> datetime | None:
    if current is None:
        return candidate
    if candidate is None:
        return current
    return candidate if candidate > current else current
