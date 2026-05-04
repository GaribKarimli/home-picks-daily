import re
import random
from typing import Optional

import requests
from bs4 import BeautifulSoup

from scripts.config import Config, NICHES, SMART_FILTERS


def _headers() -> dict:
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0.6099.43 Mobile Safari/537.36",
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }


def _parse_price(price_str: str) -> Optional[float]:
    if not price_str:
        return None
    match = re.search(r"[\d,]+\.?\d*", price_str.replace(",", ""))
    if match:
        return float(match.group())
    return None


def _parse_review_count(text: str) -> int:
    match = re.search(r"([\d,]+)", text.replace(",", ""))
    if match:
        return int(match.group(1))
    return 0


def _passes_smart_filter(rating: float, reviews: int, price_num: Optional[float]) -> bool:
    if rating < SMART_FILTERS["min_rating"]:
        return False
    if reviews < SMART_FILTERS["min_reviews"]:
        return False
    if price_num is not None:
        if price_num < SMART_FILTERS["min_price"] or price_num > SMART_FILTERS["max_price"]:
            return False
    return True


def _is_valid_image_url(url: str) -> bool:
    if not url:
        return False
    if not url.startswith("http"):
        return False
    ext = url.lower().rsplit("?", 1)[0].rsplit(".", 1)
    if len(ext) < 2:
        return False
    return ext[1] in {"jpg", "jpeg", "png"}


def _build_amazon_url(asin: str) -> str:
    base = f"https://www.amazon.com/dp/{asin}"
    tag = Config.AMAZON_TAG
    return f"{base}/?tag={tag}"


def _verify_link(url: str, timeout: int = 5) -> bool:
    try:
        resp = requests.head(url, headers=_headers(), timeout=timeout, allow_redirects=True)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def search_amazon(keyword: str, max_results: int = 5) -> list[dict]:
    url = f"https://www.amazon.com/s?k={keyword}&ref=nb_sb_noss"
    try:
        resp = requests.get(url, headers=_headers(), timeout=15)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    products = []
    cards = soup.select("[data-asin]:not([data-asin=''])")

    for card in cards:
        if len(products) >= max_results:
            break

        asin = card.get("data-asin", "")
        if not asin or len(asin) < 10:
            continue

        title_el = card.select_one("h2 a.a-link-normal span.a-text-normal") or card.select_one("h2 a span")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)

        img_el = card.select_one("img.s-image")
        src = img_el.get("src", "") if img_el else ""
        data_src = img_el.get("data-src", "") if img_el else ""
        image = data_src or src

        price_el = card.select_one("span.a-price span.a-offscreen")
        price = price_el.get_text(strip=True) if price_el else ""
        price_num = _parse_price(price)

        rating_el = card.select_one("i.a-icon-star span.a-icon-alt")
        rating = 0.0
        if rating_el:
            match = re.search(r"([\d.]+)", rating_el.get_text())
            if match:
                rating = float(match.group(1))

        review_el = card.select_one("a.a-link-normal.s-underline-text > span")
        reviews = _parse_review_count(review_el.get_text(strip=True)) if review_el else 0

        if not _passes_smart_filter(rating, reviews, price_num):
            continue

        if not _is_valid_image_url(image):
            print(f"  [X] Invalid image URL for '{title[:50]}'. Skipping.")
            continue

        amazon_link = _build_amazon_url(asin)
        if not _verify_link(amazon_link):
            print(f"  [X] Amazon link unreachable for '{title[:50]}'. Skipping.")
            continue

        products.append({
            "title": title,
            "price": price or f"${price_num:.2f}" if price_num else "",
            "rating": rating,
            "reviews": reviews,
            "image": image,
            "url": amazon_link,
            "asin": asin,
        })

    return products


def get_products(
    niche: str = "home-decor",
    count: int = 3,
    search_terms: list[str] | None = None,
) -> list[dict]:
    niche_config = NICHES.get(niche, NICHES["home-decor"])

    terms = search_terms if search_terms else niche_config["search_terms"]
    all_products = []

    for term in terms:
        products = search_amazon(term, max_results=count)
        all_products.extend(products)
        if len(all_products) >= count:
            break

    if not all_products:
        print("  [X] Amazon scraping returned no results. No products to add.")
        return []

    all_products.sort(key=lambda p: (1 if p["image"] else 0, p["rating"]), reverse=True)
    return all_products[:count]
