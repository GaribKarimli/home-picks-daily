import re
from datetime import date

from google import genai

from scripts.config import Config

CATEGORY_MAP = {
    "kitchen-gadgets": "Kitchen Gadgets",
    "living-room-decor": "Living Room Decor",
    "organization-hacks": "Organization Hacks",
}

POST_SYSTEM_PROMPT = """You are a professional content writer for a minimalist home & kitchen affiliate website called "Home Picks Daily". Your audience comes from Pinterest — they love aesthetic, warm, minimalist content.

Write product content in Azerbaijani language with the following rules:
- Tone: warm, minimalist, premium, aspirational
- Focus on how the product enhances daily home living
- Keep sentences short and visual (Pinterest-friendly)
- Never mention price or discounts in the body
- Never use emojis

Generate exactly these fields in your response (use the exact labels):

BASLIQ: <SEO-friendly title, max 60 chars, in Azerbaijani>

QIYMET: <same price as input>

XUSUSIYYETLER:
- <feature 1>
- <feature 2>
- <feature 3>
- <feature 4>
- <feature 5>

METADESC: <one sentence, max 160 chars, in Azerbaijani>

MEQALE:
<2-3 short paragraphs describing the product, its aesthetic value, and how it transforms home living. Write in Azerbaijani.>
"""


def _build_product_prompt(product: dict) -> str:
    return f"""Product information:

Title: {product['title']}
Price: {product['price']}
Rating: {product['rating']}/5
Category: Home & Kitchen

{POST_SYSTEM_PROMPT}"""


def generate_post(product: dict, category_slug: str) -> dict:
    try:
        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        prompt = _build_product_prompt(product)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        text = response.text.strip()
        return _parse_response(text, product, category_slug)
    except Exception as e:
        print(f"  [WARN] Gemini API call failed: {e}")
        print(f"  [~] Using fallback content for: {product['title']}")
        return _fallback_post(product, category_slug)


def _fallback_post(product: dict, category_slug: str) -> dict:
    category_name = CATEGORY_MAP.get(category_slug, "Home & Kitchen")
    slug = _to_slug(product["title"])
    amazon_link = f"https://www.amazon.com/dp/{product['asin']}/?tag={Config.AMAZON_TAG}"
    return {
        "title": product["title"],
        "slug": slug,
        "image": product["image"],
        "price": product["price"],
        "amazonLink": amazon_link,
        "category": category_name,
        "features": ["Premium quality", "Minimalist design", "Durable materials"],
        "rating": product["rating"],
        "date": date.today().isoformat(),
        "description": f"Discover the {product['title']} - the perfect addition to your home.",
        "body": f"Write your product description here for {product['title']}...",
    }


def _parse_response(text: str, product: dict, category_slug: str) -> dict:
    category_name = CATEGORY_MAP.get(category_slug, "Home & Kitchen")

    title = _extract_field(text, "BASLIQ", product["title"])
    meta_desc = _extract_field(text, "METADESC", "")
    features_text = _extract_field(text, "XUSUSIYYETLER", "")
    features = [
        f.strip("- ").strip()
        for f in features_text.split("\n")
        if f.strip() and f.strip().startswith("-")
    ]
    if not features:
        features = ["Premium quality", "Minimalist design", "Durable materials"]

    body = _extract_field(text, "MEQALE", "Write your product description here...")

    slug = _to_slug(title)

    amazon_link = f"https://www.amazon.com/dp/{product['asin']}/?tag={Config.AMAZON_TAG}"

    return {
        "title": title,
        "slug": slug,
        "image": product["image"],
        "price": product["price"],
        "amazonLink": amazon_link,
        "category": category_name,
        "features": features,
        "rating": product["rating"],
        "date": date.today().isoformat(),
        "description": meta_desc,
        "body": body,
    }


def _extract_field(text: str, label: str, fallback: str) -> str:
    pattern = rf"{label}:\s*(.+?)(?=\n[A-Z]+:|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return fallback


def _to_slug(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9 a-zəçəıüöğş]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return slug[:80]
