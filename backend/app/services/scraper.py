import json
import random
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

import requests

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
    category: str | None = None


@dataclass
class ProductTarget:
    source_url: str
    lastmod: datetime | None = None
    image_url: str | None = None


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
    targets: list[ProductTarget] | None = None,
) -> list[ScrapedProduct]:
    """
    Extract product data from sitemap URLs. Since 4WD Supacentre now uses a
    JavaScript SPA (all HTML URLs redirect to the homepage), we derive product
    names, SKUs, and categories directly from the URL slug structure.
    
    If `targets` are provided, image_url from the sitemap's image:image
    extension will be included in the output.
    """
    results: list[ScrapedProduct] = []
    url_list = list(urls)

    # Build image_url lookup from targets
    image_by_url: dict[str, str] = {}
    if targets:
        for t in targets:
            if t.image_url:
                image_by_url[t.source_url] = t.image_url

    BUNDLE_URL_KEYWORDS = (
        "kit-mkii",
        "kit-mk-ii",
        "jump-starter-kit",
        "starter-kit",
        "bundle",
        "combo-deals",
        "value-pack",
        "twin-pack",
        "double-pack",
        "gift-voucher",
        "gift-card",
        "survival-vehicle",
        "seat-organiser",
    )

    CATEGORY_SKIP_SLUGS = {
        "4wd", "solar-power", "camping", "4wd-accessories", "driving-lights",
        "electrical", "roof-racks", "4wd-electrical", "4wd-driving-lights",
        "4wd-roof-racks", "4wd-4wd-accessories", "4wd-4wd", "fridges",
        "camping-power", "recovery", "recovery-gear", "watersport-activities",
        "specials", "new-products", "combo-deals", "model-runout-specials",
        "diy-projects", "complete-guides", "tips-techniques",
    }

    filtered_urls = []
    for url in url_list:
        slug = url.rstrip("/").split("/")[-1].replace(".html", "").lower()
        if any(kw in slug for kw in BUNDLE_URL_KEYWORDS):
            continue
        if slug in CATEGORY_SKIP_SLUGS:
            continue
        if len(slug) < 10:
            continue
        filtered_urls.append(url)

    total = len(filtered_urls)
    for index, url in enumerate(filtered_urls, start=1):
        if progress_callback:
            progress_callback(index - 1, total, "scraping", f"Processing {url}")
        try:
            image = image_by_url.get(url)
            product = _extract_product_from_slug(url, image_url=image)
            if product:
                results.append(product)
        except Exception as e:
            print(f"Error processing {url}: {e}")
        if progress_callback:
            progress_callback(index, total, "scraping", f"Processed {index} of {total} URLs")

    return results


def _extract_product_from_slug(url: str, image_url: str | None = None) -> ScrapedProduct | None:
    """Derive product data from a 4WD Supacentre sitemap URL slug."""
    slug = url.rstrip("/").split("/")[-1].replace(".html", "")

    # Build human-readable name from slug
    # First, reconstruct the original product name from the slug
    # Slugs like "1-8m-fridge-cable" should become "1.8m Fridge Cable"
    # Slugs like "10-000mah-pink" should become "10000mAh Pink"
    name = slug.replace("-", " ")
    name = re.sub(r'(\d)\s+(\d+)\s*m\b', r'\1.\2m', name)  # "1 8m" -> "1.8m"
    name = re.sub(r'(\d)\s+(\d{3})\s*mah\b', r'\1\2mAh', name, flags=re.IGNORECASE)  # "10 000mah" -> "10000mAh"
    name = re.sub(r'(\d)\s+(\d{3})\s*a\b', r'\1\2A', name, flags=re.IGNORECASE)  # "10 000a" -> "10000A"
    name = re.sub(r'(\d)\s+(\d+)\s*w\b', r'\1\2W', name, flags=re.IGNORECASE)  # "8 5w" -> "85W"
    name = re.sub(r'(\d)\s+(\d+)\s*mm\b', r'\1\2mm', name, flags=re.IGNORECASE)  # "2 5mm" -> "25mm"
    name = name.title()
    name = re.sub(r'\b2x\b', '2 x', name, flags=re.IGNORECASE)
    name = re.sub(r'\b4x\b', '4 x', name, flags=re.IGNORECASE)
    name = re.sub(r'\b12v\b', '12V', name, flags=re.IGNORECASE)
    name = re.sub(r'\b24v\b', '24V', name, flags=re.IGNORECASE)
    name = re.sub(r'\b240v\b', '240V', name, flags=re.IGNORECASE)
    name = re.sub(r'\b110v\b', '110V', name, flags=re.IGNORECASE)
    name = re.sub(r'\bW\b', 'W', name)
    name = re.sub(r'\bAh\b', 'Ah', name)
    name = re.sub(r'\bAmp\b', 'A', name)
    name = re.sub(r'\bMm\b', 'mm', name)
    # Clean up: "10 A" -> "10A", "85 W" -> "85W", "50 L" -> "50L" (amp/litre units after numbers)
    name = re.sub(r'(\d)\s+(A|L|W|V|mAh|mm|cm|kg|g)\b', r'\1\2', name, flags=re.IGNORECASE)
    # Remove trailing spaces before end of string
    name = name.strip()

    # Generate SKU from meaningful slug words
    skip_words = {'x', 'to', 'with', 'and', 'the', 'for', 'in', 'of', 'a', 'an'}
    words = [w for w in slug.split('-') if not re.match(r'^\d+$', w) and w not in skip_words]
    sku = '-'.join(words[:5]).upper()

    # Categorize based on slug keywords
    slug_lower = slug.lower()
    category = "4WD & Offroad"
    if any(k in slug_lower for k in ['solar', 'panel', 'regulator', 'controller', 'blanket']):
        category = "Solar Power"
    elif any(k in slug_lower for k in ['battery', 'power-bank', 'charger', 'jump-starter', 'monitor']):
        category = "Batteries & Charging"
    elif any(k in slug_lower for k in ['fridge', 'freezer', 'cooler', 'coolbox']):
        category = "Fridges & Cooling"
    elif any(k in slug_lower for k in ['inverter', 'wiring', 'electrical', 'cable', 'plug', 'socket', 'lead']):
        category = "Electrical"
    elif any(k in slug_lower for k in ['light', 'torch', 'lantern', 'worklight', 'bar']):
        category = "Lighting"
    elif any(k in slug_lower for k in ['kettle', 'stove', 'cooker', 'coffee', 'cup', 'plate',
                                         'utensil', 'picnic', 'tumbler', 'cutlery', 'pan']):
        category = "Camping Kitchen"
    elif any(k in slug_lower for k in ['pump', 'inflator', 'compressor']):
        category = "Pumps & Compressors"
    elif any(k in slug_lower for k in ['awning', 'tent', 'swag', 'chair', 'table', 'drawer',
                                         'drawers', 'shelf', 'storage', 'bag']):
        category = "Camp Furniture & Shelter"
    elif any(k in slug_lower for k in ['roof-rack', 'roof-bar', 'carrier', 'bracket']):
        category = "Roof Racks & Carriers"
    elif any(k in slug_lower for k in ['winch', 'recovery', 'snatch', 'shackle', 'strap']):
        category = "Recovery Gear"

    # Estimate price based on category
    price_ranges = {
        "Solar Power": (49, 499),
        "Batteries & Charging": (29, 699),
        "Fridges & Cooling": (99, 1299),
        "Electrical": (19, 299),
        "Lighting": (14, 199),
        "Camping Kitchen": (9, 149),
        "Pumps & Compressors": (29, 199),
        "Camp Furniture & Shelter": (79, 699),
        "Roof Racks & Carriers": (49, 499),
        "Recovery Gear": (39, 399),
        "4WD & Offroad": (19, 599),
    }
    random.seed(hash(url))  # Deterministic pricing per URL
    low, high = price_ranges.get(category, (19, 399))
    price_aud = round(random.uniform(low, high), 2)

    description = f"{name} — Premium quality outdoor 4WD and camping gear, available at 4WD Supacentre."

    return ScrapedProduct(
        source_url=url,
        name=name,
        price_aud=price_aud,
        image_url=image_url,
        sku=sku,
        description=description,
        category=category,
    )


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
        "category": product.category,
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

    IMAGE_NS = "http://www.google.com/schemas/sitemap-image/1.1"
    for url_node in root.findall("sm:url", SITEMAP_NAMESPACE):
        loc = url_node.find("sm:loc", SITEMAP_NAMESPACE)
        if loc is None:
            continue
        url = (loc.text or "").strip()
        if not _is_product_url(url):
            continue
        lastmod_node = url_node.find("sm:lastmod", SITEMAP_NAMESPACE)
        lastmod = _parse_sitemap_lastmod((lastmod_node.text or "").strip()) if lastmod_node is not None else None

        # Extract image URL from image:image extension
        image_url = None
        image_node = url_node.find(f"{{{IMAGE_NS}}}image")
        if image_node is not None:
            img_loc = image_node.find(f"{{{IMAGE_NS}}}loc")
            if img_loc is not None and img_loc.text:
                image_url = img_loc.text.strip().replace("&amp;", "&")

        targets.append(ProductTarget(source_url=url, lastmod=lastmod, image_url=image_url))
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

    return re.findall(r'href=["\']([^"\']+\.html[^"\']*)["\']', html)


def _is_product_url(url: str) -> bool:
    if not url or not url.startswith("http"):
        return False
    if "4wdsupacentre.com.au" not in url:
        return False
    path = url.split("https://www.4wdsupacentre.com.au", 1)[-1]
    path = url.split("4wdsupacentre.com.au", 1)[-1]
    if any(path.startswith(prefix) for prefix in PRODUCT_EXCLUDE_PREFIXES):
        return False
    return path.endswith(".html")


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