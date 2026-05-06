import re
import json
import random
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


MANUAL_TITLES = {
    "B0D3W6XGLR": "DASH Rapid Egg Cooker",
    "B08573DQ39": "Umite Chef Kitchen Utensils Set",
    "B07VWL357N": "O-Cedar EasyWring Microfiber Spin Mop",
}


ASINS = [
    "B0D3W6XGLR",
    "B08573DQ39",
    "B0FR4NZN55",
    "B06X9NQ8GX",
    "B07VWL357N",
    "B0C3QZ7SNF",
    "B0BWHJ1FNK",
    "B0GW7BF6YF",
    "B09B2QTGFY",
    "B0D6D76THV",
    "B0FH6YL3XC",
    "B0764HS4SL",
    "B0FLVHKKG5",
    "B0FBWFB42X",
    "B0D3PWHQD9",
    "B0GWF75Z2J",
    "B0CJF94M8J",
    "B012T634SM",
    "B0B2K47S1T",
    "B0DNTQ2YNT",
    "B0F2TB2MMP",
    "B0DJSQQ1ZW",
    "B0D9B96TBX",
    "B0CZPGJ2JW",
    "B016OP6N3M",
]


def _headers():
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


def fetch_asin_data(asin: str) -> dict | None:
    url = f"https://www.amazon.com/dp/{asin}"
    print(f"  [>] Fetching {asin}...", end=" ")
    try:
        resp = requests.get(url, headers=_headers(), timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"FAILED ({e})")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    title_el = soup.select_one("#productTitle")
    title = title_el.get_text(strip=True) if title_el else MANUAL_TITLES.get(asin, "")

    img_el = soup.select_one("#landingImage")
    image = ""
    if img_el:
        image = img_el.get("src", "") or img_el.get("data-old-hires", "")

    if not image:
        img_el = soup.select_one("img.a-dynamic-image")
        if img_el:
            image = img_el.get("src", "") or img_el.get("data-old-hires", "")

    if not image:
        alt_img = soup.select_one("div.imgTagWrapper img")
        if alt_img:
            image = alt_img.get("src", "")

    if image:
        image = image.split("_")[0] + "_AC_SL1500_.jpg"

    if not image.startswith("https://m.media-amazon.com"):
        print(f"SKIPPED - no real Amazon image")
        return None

    print(f"OK - {title[:50]}")
    return {"asin": asin, "title": title, "image": image}


def load_json():
    path = Path("scripts/my_products.json")
    if not path.exists():
        return {"products": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(data: dict):
    path = Path("scripts/my_products.json")
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  [OK] Saved to {path}")


def main():
    data = load_json()
    existing_asins = {p["asin"] for p in data["products"]}

    for i, asin in enumerate(ASINS, 1):
        print(f"\n[{i}/{len(ASINS)}] ", end="")
        if asin in existing_asins:
            print(f"Skipping {asin} (already in JSON)")
            continue
        result = fetch_asin_data(asin)
        if result:
            data["products"].append({
                "title": result["title"],
                "price": "",
                "rating": 0.0,
                "reviews": 0,
                "image": result["image"],
                "asin": result["asin"],
            })
        time.sleep(random.uniform(2, 4))

    save_json(data)
    print(f"  [OK] Total products in JSON: {len(data['products'])}")


if __name__ == "__main__":
    main()
