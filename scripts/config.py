import os
from dotenv import load_dotenv

load_dotenv()

NICHES = {
    "home-decor": {
        "name": "Home Decor",
        "amazon_category": "Home & Kitchen",
        "search_terms": ["home+decor+trending", "living+room+decor", "wall+art+home"],
        "trends_keywords": ["home decor", "interior design", "living room decor", "wall art"],
        "demo_products_idx": [0, 1],
    },
    "tech-gadgets": {
        "name": "Tech Gadgets",
        "amazon_category": "Electronics",
        "search_terms": ["tech+gadgets+2026", "smart+home+devices", "cool+gadgets+men"],
        "trends_keywords": ["tech gadgets", "smart home", "gadgets 2026", "wireless earbuds"],
        "demo_products_idx": [2, 3],
    },
    "fitness-equipment": {
        "name": "Fitness Equipment",
        "amazon_category": "Sports & Outdoors",
        "search_terms": ["home+gym+equipment", "fitness+gear+women", "workout+accessories"],
        "trends_keywords": ["home gym", "fitness equipment", "workout gear", "yoga mat"],
        "demo_products_idx": [4, 0],
    },
    "kitchen-essentials": {
        "name": "Kitchen Essentials",
        "amazon_category": "Kitchen & Dining",
        "search_terms": ["kitchen+essentials", "cooking+tools+trending", "kitchen+gadgets+amazon"],
        "trends_keywords": ["kitchen gadgets", "cooking tools", "baking essentials", "meal prep"],
        "demo_products_idx": [1, 3],
    },
}

SMART_FILTERS = {
    "min_rating": 4.0,
    "min_reviews": 500,
    "min_price": 30,
    "max_price": 500,
}


class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    AMAZON_TAG: str = os.getenv("AMAZON_TAG", "dummy-20")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    REPO_PATH: str = os.getenv("REPO_PATH", "GaribKarimli/home-picks-daily")
    SITE_URL: str = "https://home-picks-daily.vercel.app"
    LOCAL_REPO_DIR: str = "repo_cache"

    @classmethod
    def validate(cls):
        missing = []
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if not cls.GITHUB_TOKEN:
            missing.append("GITHUB_TOKEN")
        if missing:
            raise ValueError(
                f"Missing required env vars: {', '.join(missing)}. "
                f"Check your .env file."
            )
