import re
import random
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

from scripts.config import Config


DEMO_PRODUCTS = [
    {
        "title": "Smart Kitchen Scale with Nutritional Database",
        "price": "$29.99",
        "rating": 4.5,
        "image": "https://images.unsplash.com/photo-1584479898061-15742e1c2180?w=800&q=80",
        "url": "https://www.amazon.com/dp/B0EXAMPLE1",
        "asin": "B0EXAMPLE1",
    },
    {
        "title": "Minimalist Bamboo Wall Clock Silent Movement",
        "price": "$39.99",
        "rating": 4.7,
        "image": "https://images.unsplash.com/photo-1565193566173-7a0ee3dbea78?w=800&q=80",
        "url": "https://www.amazon.com/dp/B0EXAMPLE2",
        "asin": "B0EXAMPLE2",
    },
    {
        "title": "Modular Bamboo Drawer Organizer Set of 8",
        "price": "$24.99",
        "rating": 4.3,
        "image": "https://images.unsplash.com/photo-1586105251261-72a756497a11?w=800&q=80",
        "url": "https://www.amazon.com/dp/B0EXAMPLE3",
        "asin": "B0EXAMPLE3",
    },
    {
        "title": "French Press Coffee Maker Borosilicate Glass",
        "price": "$34.95",
        "rating": 4.6,
        "image": "https://images.unsplash.com/photo-1564758562183-1c1e2e1b3843?w=800&q=80",
        "url": "https://www.amazon.com/dp/B0EXAMPLE4",
        "asin": "B0EXAMPLE4",
    },
    {
        "title": "Scented Soy Candle Set Lavender & Vanilla",
        "price": "$19.99",
        "rating": 4.4,
        "image": "https://images.unsplash.com/photo-1602874801007-bd36c3e2a2ad?w=800&q=80",
        "url": "https://www.amazon.com/dp/B0EXAMPLE5",
        "asin": "B0EXAMPLE5",
    },
]

CATEGORY_KEYWORDS = {
    "kitchen-gadgets": "kitchen+gadgets+home",
    "living-room-decor": "living+room+decor+home",
    "organization-hacks": "home+organization+storage",
}


def _headers() -> dict:
    mobile_agents = [
        "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0.6099.43 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Mobile/15E148",
        "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/121.0.6167.101 Mobile Safari/537.36",
    ]
    return {
        "User-Agent": random.choice(mobile_agents),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }


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

        title_el = card.select_one("h2 a.a-link-normal span.a-text-normal")
        if not title_el:
            title_el = card.select_one("h2 a span")
        if not title_el:
            continue

        title = title_el.get_text(strip=True)

        img_el = card.select_one("img.s-image")
        image = img_el.get("src", "") if img_el else ""

        price_el = card.select_one("span.a-price span.a-offscreen")
        price = price_el.get_text(strip=True) if price_el else ""

        rating_el = card.select_one("i.a-icon-star span.a-icon-alt")
        rating = 0.0
        if rating_el:
            match = re.search(r"([\d.]+)", rating_el.get_text())
            if match:
                rating = float(match.group(1))

        url = f"https://www.amazon.com/dp/{asin}"

        products.append({
            "title": title,
            "price": price,
            "rating": rating,
            "image": image,
            "url": url,
            "asin": asin,
        })

    return products


def get_products(
    category: str = "kitchen-gadgets",
    count: int = 3,
    demo: bool = False,
) -> list[dict]:
    if demo:
        return DEMO_PRODUCTS[:count]

    keyword = CATEGORY_KEYWORDS.get(category, category.replace("-", "+"))
    products = search_amazon(keyword, max_results=count)

    if not products:
        print("  [X] Amazon scraping returned no results. Falling back to demo data.")
        return DEMO_PRODUCTS[:count]

    return products
