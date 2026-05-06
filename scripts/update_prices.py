import json, re, time, random
from pathlib import Path
import requests
from bs4 import BeautifulSoup


def _headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0.6099.43 Mobile Safari/537.36",
    ]
    return {"User-Agent": random.choice(user_agents), "Accept-Language": "en-US,en;q=0.9"}


def scrape_asin(asin: str):
    url = f"https://www.amazon.com/dp/{asin}"
    print(f"  [>] {asin}...", end=" ", flush=True)
    try:
        resp = requests.get(url, headers=_headers(), timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"FAILED ({e})")
        return None
    soup = BeautifulSoup(resp.text, "lxml")

    price = ""
    el = soup.select_one(".a-price .a-offscreen")
    if el:
        price = el.get_text(strip=True)

    rating = 0.0
    el = soup.select_one("i.a-icon-star span.a-icon-alt")
    if el:
        m = re.search(r"([\d.]+)", el.get_text())
        if m:
            rating = float(m.group(1))

    reviews = 0
    el = soup.select_one("#acrCustomerReviewText")
    if el:
        m = re.search(r"([\d,]+)", el.get_text().replace(",", ""))
        if m:
            reviews = int(m.group(1))

    print(f"${price} | {rating}/5 ({reviews} reviews)" if price else f"? | {rating}/5 ({reviews} reviews)")
    return {"price": price, "rating": rating, "reviews": reviews}


def main():
    path = Path("scripts/my_products.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    for i, p in enumerate(data["products"], 1):
        print(f"[{i}/{len(data['products'])}] ", end="")
        asin = p["asin"]
        result = scrape_asin(asin)
        if result:
            p["price"] = result["price"] or p["price"]
            p["rating"] = result["rating"] or p["rating"]
            p["reviews"] = result["reviews"] or p["reviews"]
        time.sleep(random.uniform(1.5, 3))
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  [OK] Updated {path}")


if __name__ == "__main__":
    main()
