#!/usr/bin/env python3
"""
Home Picks Daily - Amazon Affiliate Content Automation

Usage:
  python -m scripts.main --category kitchen-gadgets --count 3 --demo
  python -m scripts.main --category living-room-decor --count 5
  python -m scripts.main --category organization-hacks --count 2 --no-push
"""

import argparse
import sys
from pathlib import Path

from scripts.config import Config
from scripts.scraper import get_products
from scripts.generator import generate_post
from scripts.github_client import push_product

CHECK = "[OK]"
CROSS = "[X]"
ARROW = "[>]"
STAR = "[*]"


def build_markdown(post: dict) -> str:
    features_yaml = "\n".join(f'  - "{f}"' for f in post["features"])

    return f"""---
title: "{post['title']}"
image: "{post['image']}"
price: "{post['price']}"
amazonLink: "{post['amazonLink']}"
category: "{post['category']}"
features:
{features_yaml}
rating: {post['rating']}
date: {post['date']}
description: "{post['description']}"
---

{post['body']}
"""


def run(category: str, count: int, demo: bool, push: bool):
    print(f"  {STAR} Fetching {count} products from category: {category}")
    products = get_products(category, count, demo=demo)
    print(f"  {CHECK} Got {len(products)} products\n")

    for i, product in enumerate(products, 1):
        short = product['title'][:50]
        print(f"  [{i}/{len(products)}] Generating content for: {short}...")
        post = generate_post(product, category)

        md = build_markdown(post)
        filename = f"{post['slug']}.md"

        local_path = Path("src/content/posts") / filename
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(md, encoding="utf-8")
        print(f"  {CHECK} Saved locally: {local_path}")

        if push:
            try:
                push_product(md, filename)
            except RuntimeError as e:
                print(f"  {CROSS} GitHub push failed: {e}")
                print(f"  {ARROW} File saved locally - push manually later.")
        else:
            print(f"  {ARROW} --no-push set. Skipping GitHub.\n")

    print(f"\n  {CHECK} Done! {len(products)} post(s) generated.")


def main():
    parser = argparse.ArgumentParser(
        description="Home Picks Daily - AI-powered Amazon affiliate content generator"
    )
    parser.add_argument(
        "--category",
        default="kitchen-gadgets",
        choices=["kitchen-gadgets", "living-room-decor", "organization-hacks"],
        help="Product category (default: kitchen-gadgets)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="Number of products to process (default: 3)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use demo products instead of live Amazon scraping",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Skip GitHub push (save files locally only)",
    )
    args = parser.parse_args()

    try:
        Config.validate()
    except ValueError as e:
        print(f"[ERROR] {e}")
        if args.demo:
            print(f"[~] Continuing in demo mode with local save only...")
        else:
            sys.exit(1)

    run(
        category=args.category,
        count=args.count,
        demo=args.demo,
        push=not args.no_push,
    )


if __name__ == "__main__":
    main()
