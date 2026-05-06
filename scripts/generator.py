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
    # 1) Try Amazon scraping first (always available, no API key needed)
    result = _try_amazon_description(product, niche)
    if result:
        return result

    prompt = _build_product_prompt(product, niche)

    # 2) Try Groq
    if Config.GROQ_API_KEY:
        result = _try_groq(prompt, product, niche)
        if result:
            return result

    # 3) Try Gemini
    if Config.GEMINI_API_KEY:
        result = _try_gemini(prompt, product, niche)
        if result:
            return result

    # 4) Template-based fallback
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


def _try_amazon_description(product: dict, niche: str) -> Optional[dict]:
    asin = product.get("asin", "")
    if not asin:
        return None
    url = f"https://www.amazon.com/dp/{asin}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        import requests
        from bs4 import BeautifulSoup
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        desc_el = None
        for sel in ["#productDescription", "#feature-bullets"]:
            desc_el = soup.select_one(sel)
            if desc_el:
                break
        if not desc_el:
            return None
        body = desc_el.get_text(strip=True, separator=" ")
        body = re.sub(r"\s+", " ", body).strip()
        if len(body) < 100:
            return None
        print(f"  [~] Using Amazon description for: {product['title']}")
        return _build_post(product, niche, body)
    except Exception:
        return None


def _build_post(product: dict, niche: str, body: str) -> dict:
    niche_name = NICHE_DISPLAY.get(niche, "Home & Kitchen")
    slug = _to_slug(product["title"])
    amazon_link = f"https://www.amazon.com/dp/{product['asin']}/?tag={Config.AMAZON_TAG}"
    description = body[:160].rsplit(" ", 1)[0] + "..." if len(body) > 160 else body
    return {
        "title": product["title"],
        "slug": slug,
        "image": product["image"],
        "price": product["price"],
        "amazonLink": amazon_link,
        "niche": niche,
        "category": niche_name,
        "features": _generate_fallback_features(product["title"], niche_name),
        "rating": product["rating"],
        "reviews": product.get("reviews", 0),
        "date": date.today().isoformat(),
        "description": description,
        "body": body,
    }


def _fallback_post(product: dict, niche: str) -> dict:
    niche_name = NICHE_DISPLAY.get(niche, "Home & Kitchen")
    slug = _to_slug(product["title"])
    amazon_link = f"https://www.amazon.com/dp/{product['asin']}/?tag={Config.AMAZON_TAG}"
    title = product["title"]
    desc = f"Elevate your {niche_name.lower()} with this thoughtfully designed product."
    body = _generate_fallback_body(title, niche_name)
    return {
        "title": title,
        "slug": slug,
        "image": product["image"],
        "price": product["price"],
        "amazonLink": amazon_link,
        "niche": niche,
        "category": niche_name,
        "features": _generate_fallback_features(title, niche_name),
        "rating": product["rating"],
        "reviews": product.get("reviews", 0),
        "date": date.today().isoformat(),
        "description": desc,
        "body": body,
    }


def _generate_fallback_features(title: str, niche: str) -> list[str]:
    t = title.lower()
    features = []
    if "set" in t or "kit" in t or "pcs" in t or "piece" in t:
        features.append(f"Complete {niche.lower()} set with multiple pieces")
    if "stainless" in t or "steel" in t:
        features.append("Crafted from premium stainless steel for lasting durability")
    if "non-stick" in t or "nonstick" in t:
        features.append("Non-stick surface for effortless cooking and easy cleaning")
    if "silicone" in t:
        features.append("Food-grade silicone, heat-resistant up to high temperatures")
    if "bamboo" in t:
        features.append("Sustainable bamboo construction, naturally anti-bacterial")
    if "digital" in t or "smart" in t or "display" in t:
        features.append("Advanced digital interface for precise control")
    if "portable" in t or "compact" in t or "small" in t:
        features.append("Space-saving compact design, perfect for any kitchen")
    if "organizer" in t or "storage" in t or "holder" in t:
        features.append("Smart organization solution for a clutter-free space")
    if "cleaner" in t or "steam" in t or "mop" in t:
        features.append("Powerful cleaning performance for a sparkling home")
    if "blender" in t or "mixer" in t or "chopper" in t:
        features.append("Powerful motor for effortless blending and mixing")
    if "toaster" in t:
        features.append("Even toasting with adjustable shade settings")
    if "scale" in t:
        features.append("Accurate measurements for precise cooking and baking")
    if "echo" in t or "alexa" in t:
        features.append("Voice-controlled smart display with Alexa built-in")
    if "grinder" in t or "salt" in t or "pepper" in t:
        features.append("Adjustable coarseness for the perfect grind every time")
    if "parchment" in t or "paper" in t:
        features.append("Unbleached, non-stick surface for healthy baking")
    if "sponge" in t:
        features.append("Odor-resistant and long-lasting for daily kitchen use")
    if "sprayer" in t or "dispenser" in t or "oil" in t:
        features.append("Precise dispensing for controlled portioning")
    if not features:
        features.append(f"Premium quality {niche.lower()} product")
        features.append("Designed for everyday convenience and lasting performance")
    if len(features) < 4:
        features.append("Easy to clean and maintain for long-term use")
        features.append(f"Versatile design that complements any {niche.lower()} style")
    return features[:5]


def _generate_fallback_body(title: str, niche: str) -> str:
    t = title.lower()
    paragraphs = []
    if "organizer" in t or "storage" in t or "holder" in t or "caddy" in t:
        paragraphs.append(
            f"Transform your space with the {title}. "
            f"This thoughtfully designed organizer brings both style and functionality to your daily routine. "
            f"Built with quality materials and a keen eye for detail, it helps you maintain a tidy, clutter-free environment effortlessly."
        )
        paragraphs.append(
            f"Whether you are tidying up your countertops or organizing your cabinets, "
            f"this solution adapts to your needs. "
            f"Its sleek design blends seamlessly with any decor, making organization a pleasure rather than a chore."
        )
    elif "cleaner" in t or "steam" in t or "mop" in t or "scrub" in t:
        paragraphs.append(
            f"Meet the {title} \u2014 your new go-to for effortless cleaning. "
            f"Designed to tackle tough dirt and grime, this powerful tool makes household cleaning faster and more effective. "
            f"From kitchen counters to bathroom tiles, it delivers sparkling results every time."
        )
        paragraphs.append(
            f"With user-friendly features and durable construction, this cleaning essential "
            f"is built to last. Save time and energy while achieving professional-level cleanliness throughout your home."
        )
    elif "blender" in t or "mixer" in t or "chopper" in t or "cooker" in t or "toaster" in t:
        paragraphs.append(
            f"The {title} is here to simplify your time in the kitchen. "
            f"Whether you are preparing a quick breakfast or an elaborate dinner, this appliance delivers consistent, reliable results. "
            f"Its intuitive design makes it easy for anyone to use, from beginners to seasoned home cooks."
        )
        paragraphs.append(
            f"Compact yet powerful, it takes up minimal counter space while offering maximum performance. "
            f"Elevate your cooking experience with a tool that works as hard as you do."
        )
    elif "echo" in t or "alexa" in t or "smart" in t or "display" in t:
        paragraphs.append(
            f"Experience the convenience of the {title}. "
            f"With voice control, smart home integration, and a vibrant display, this device puts information and entertainment at your fingertips. "
            f"Perfect for busy households looking to streamline their daily routines."
        )
        paragraphs.append(
            f"From setting timers and playing music to controlling compatible smart devices, "
            f"it is like having a personal assistant in every room."
        )
    elif "scale" in t or "digital" in t:
        paragraphs.append(
            f"The {title} combines precision with elegant design. "
            f"Whether you are weighing ingredients for a recipe or tracking portions, this scale delivers accurate readings every time. "
            f"Its sleek profile looks beautiful on any countertop."
        )
        paragraphs.append(
            f"Features include a clear LCD display, easy-to-use controls, and multiple measurement units. "
            f"A must-have tool for anyone who loves to cook or bake."
        )
    elif "bowl" in t or "utensil" in t or "knife" in t or "cutting" in t:
        paragraphs.append(
            f"Upgrade your kitchen with the {title}. "
            f"Made from high-quality materials, this set is designed to withstand daily use while maintaining its beautiful appearance. "
            f"Each piece is crafted with care to ensure comfort and functionality."
        )
        paragraphs.append(
            f"Whether you are prepping ingredients or serving a meal, "
            f"this collection makes every task easier and more enjoyable."
        )
    elif "grinder" in t or "salt" in t or "pepper" in t or "spice" in t:
        paragraphs.append(
            f"Elevate your seasoning game with the {title}. "
            f"Featuring an adjustable ceramic grinding mechanism, it lets you customize the coarseness of your spices with ease. "
            f"The elegant design looks stunning on any dining table or kitchen counter."
        )
        paragraphs.append(
            f"Durable and refillable, this grinder is built to last. "
            f"Freshly ground spices make every meal more flavorful."
        )
    elif "pan" in t or "pot" in t or "cookware" in t or "pots" in t:
        paragraphs.append(
            f"The {title} brings professional-grade cooking to your home kitchen. "
            f"Crafted from premium materials with a non-stick surface, this cookware set ensures even heating and effortless food release. "
            f"Designed for durability and everyday performance."
        )
        paragraphs.append(
            f"Compatible with all stovetops including induction, this set includes everything you need to prepare delicious meals. "
            f"Easy to clean and dishwasher safe for added convenience."
        )
    else:
        paragraphs.append(
            f"Discover the {title} \u2014 a carefully selected product designed to enhance your daily life. "
            f"Combining quality craftsmanship with thoughtful design, it delivers the perfect balance of style and functionality. "
            f"Whether you are upgrading your home or looking for a thoughtful gift, this product is an excellent choice."
        )
        paragraphs.append(
            f"Built to last and easy to maintain, it is a reliable addition to your home. "
            f"Experience the difference that quality makes."
        )

    paragraphs.append(
        f"Click the link above to check the current price and availability on Amazon. "
        f"Read customer reviews to see why this product is trending."
    )
    return "\n\n".join(paragraphs)


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
