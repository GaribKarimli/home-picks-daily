import re
import time
import random
from datetime import date
from typing import Optional

from google import genai as google_genai
from google.genai import errors as google_errors

from scripts.config import Config, NICHES

NICHE_DISPLAY = {k: v["name"] for k, v in NICHES.items()}

PROMPT_TEMPLATES = {
    "home-decor": "Write product content in English about home decor and interior design. Tone: warm, minimalist, premium. Focus on how the product elevates living spaces.",
    "tech-gadgets": "Write product content in English about tech gadgets. Tone: modern, innovative, premium. Focus on smart features and how the gadget simplifies daily life.",
    "fitness-equipment": "Write product content in English about fitness equipment. Tone: motivational, energetic, premium. Focus on health benefits and workout results.",
    "kitchen-essentials": "Write product content in English about kitchen essentials. Tone: warm, practical, premium. Focus on how the tool makes cooking more enjoyable.",
}

BASE_PROMPT = """You are a professional content writer for "Home Picks Daily", a multi-niche affiliate product discovery platform. Your audience comes from Pinterest — they love aesthetic, visual, premium content.

{niche_instruction}

Rules:
- Keep sentences short and visual (Pinterest-friendly)
- Never mention price or discounts in the body
- Never use emojis

Generate exactly these fields in your response (use the exact labels):

TITLE: <SEO-friendly title, max 60 chars>

PRICE: <same price as input>

FEATURES:
- <feature 1>
- <feature 2>
- <feature 3>
- <feature 4>
- <feature 5>

METADESC: <one sentence, max 160 chars>

CONTENT:
<2-3 short paragraphs describing the product and its value.>
"""


def _build_product_prompt(product: dict, niche: str) -> str:
    niche_instruction = PROMPT_TEMPLATES.get(niche, PROMPT_TEMPLATES["home-decor"])
    prompt = BASE_PROMPT.replace("{niche_instruction}", niche_instruction)

    return f"""Product information:

Title: {product['title']}
Price: {product['price']}
Rating: {product['rating']}/5

{prompt}"""


MAX_RETRIES = 3
BASE_DELAY = 2


def _is_daily_quota_error(msg: str) -> bool:
    return "per day" in msg.lower() or "limit: 0" in msg


def _parse_retry_delay(msg: str) -> float | None:
    match = re.search(r"retry in ([\d.]+)s", msg, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def generate_post(product: dict, niche: str) -> dict:
    prompt = _build_product_prompt(product, niche)

    if Config.GROQ_API_KEY:
        result = _try_groq(prompt, product, niche)
        if result:
            return result

    if Config.GEMINI_API_KEY:
        result = _try_gemini(prompt, product, niche)
        if result:
            return result

    print(f"  [~] No LLM available. Using fallback content for: {product['title']}")
    return _fallback_post(product, niche)


def _try_groq(prompt: str, product: dict, niche: str) -> Optional[dict]:
    try:
        from groq import Groq
        client = Groq(api_key=Config.GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        text = response.choices[0].message.content.strip()
        return _parse_response(text, product, niche)
    except Exception as e:
        print(f"  [WARN] Groq API call failed: {e}")
        return None


def _try_gemini(prompt: str, product: dict, niche: str) -> Optional[dict]:
    client = google_genai.Client(api_key=Config.GEMINI_API_KEY)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            text = response.text.strip()
            return _parse_response(text, product, niche)

        except google_errors.ClientError as e:
            msg = str(e)
            code = getattr(e, 'code', None) or getattr(getattr(e, 'response', None), 'status_code', 0)

            if code != 429:
                print(f"  [WARN] Gemini error (non-rate-limit): {e}")
                return None

            if _is_daily_quota_error(msg):
                print(f"  [~] Gemini daily quota exhausted. Skipping retry.")
                return None

            retry_after = _parse_retry_delay(msg)
            delay = retry_after if retry_after else BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 2)

            if attempt < MAX_RETRIES:
                print(f"  [~] Gemini rate limited (429). Retrying in {delay:.0f}s... ({attempt}/{MAX_RETRIES})")
                time.sleep(delay)
            else:
                print(f"  [WARN] Gemini rate limited after {MAX_RETRIES} retries.")

        except Exception as e:
            print(f"  [WARN] Gemini API call failed: {e}")
            return None

    return None


def _fallback_post(product: dict, niche: str) -> dict:
    niche_name = NICHE_DISPLAY.get(niche, "Home & Kitchen")
    slug = _to_slug(product["title"])
    amazon_link = f"https://www.amazon.com/dp/{product['asin']}/?tag={Config.AMAZON_TAG}"
    return {
        "title": product["title"],
        "slug": slug,
        "image": product["image"],
        "price": product["price"],
        "amazonLink": amazon_link,
        "niche": niche,
        "category": niche_name,
        "features": ["Premium quality", "Top-rated design", "Durable materials"],
        "rating": product["rating"],
        "reviews": product.get("reviews", 0),
        "date": date.today().isoformat(),
        "description": f"Discover the {product['title']} - the perfect addition to your collection.",
        "body": f"Write your product description here for {product['title']}...",
    }


def _parse_response(text: str, product: dict, niche: str) -> dict:
    niche_name = NICHE_DISPLAY.get(niche, "Home & Kitchen")
    has_trending = niche in ["tech-gadgets", "fitness-equipment"]

    title = _extract_field(text, "TITLE", product["title"])
    meta_desc = _extract_field(text, "METADESC", "")
    features_text = _extract_field(text, "FEATURES", "")
    features = [
        f.strip("- ").strip()
        for f in features_text.split("\n")
        if f.strip() and f.strip().startswith("-")
    ]
    if not features:
        features = ["Premium quality", "Top-rated design", "Durable materials"]

    body = _extract_field(text, "CONTENT", "Write your product description here...")

    slug = _to_slug(title)
    amazon_link = f"https://www.amazon.com/dp/{product['asin']}/?tag={Config.AMAZON_TAG}"

    return {
        "title": title,
        "slug": slug,
        "image": product["image"],
        "price": product["price"],
        "amazonLink": amazon_link,
        "niche": niche,
        "category": niche_name,
        "features": features,
        "rating": product["rating"],
        "reviews": product.get("reviews", 0),
        "date": date.today().isoformat(),
        "description": meta_desc,
        "trending": has_trending,
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
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return slug[:80]
