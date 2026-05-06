#!/usr/bin/env python3
"""
Home Picks Daily - Multi-Niche Affiliate Content Automation

Usage:
  python -m scripts.main --niche home-decor --count 3
  python -m scripts.main --niche tech-gadgets --count 5
  python -m scripts.main --niche fitness-equipment --count 2 --trending
  python -m scripts.main --niche kitchen-essentials --count 4 --no-push
  python -m scripts.main --all-niches --count 2 --no-push
"""

import argparse
import sys
from pathlib import Path

from scripts.config import Config, NICHES
from scripts.scraper import get_products
from scripts.generator import generate_post
from scripts.github_client import push_product
from scripts.trends import get_trending_search_terms

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
niche: "{post['niche']}"
category: "{post['category']}"
features:
{features_yaml}
rating: {post['rating']}
reviews: {post['reviews']}
date: {post['date']}
description: "{post['description']}"
trending: {"true" if post.get("trending") else "false"}
---

{post['body']}
"""


def run_niche(
    niche: str,
    count: int,
    push: bool,
    use_trends: bool,
):
    print(f"  {STAR} Niche: {NICHES[niche]['name']}")
    print(f"  {STAR} Fetching {count} products...")

    search_terms = None
    if use_trends:
        print(f"  {STAR} Checking Google Trends for {niche}...")
        search_terms = get_trending_search_terms(niche, top_n=3)
        if search_terms:
            print(f"  {CHECK} Trending terms: {', '.join(search_terms)}")

    products = get_products(niche, count, search_terms=search_terms)
    if not products:
        print(f"  {CROSS} No products found for {niche}. Product data is incomplete.")
        return

    print(f"  {CHECK} Got {len(products)} products\n")

    for i, product in enumerate(products, 1):
        short = product["title"][:50]
        print(f"  [{i}/{len(products)}] Generating content for: {short}...")
        post = generate_post(product, niche)

        md = build_markdown(post)
        filename = f"{post['slug']}.md"
        local_path = Path("src/content/posts") / niche / filename
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(md, encoding="utf-8")
        print(f"  {CHECK} Saved locally: {local_path}")

        if push:
            try:
                push_product(md, f"{niche}/{filename}")
            except RuntimeError as e:
                print(f"  {CROSS} GitHub push failed: {e}")
                print(f"  {ARROW} File saved locally - push manually later.")
        else:
            print(f"  {ARROW} --no-push set. Skipping GitHub.\n")

    print(f"  {CHECK} Done! {len(products)} post(s) for {niche}.\n")


def main():
    niche_choices = list(NICHES.keys())

    parser = argparse.ArgumentParser(
        description="Home Picks Daily - Multi-Niche Affiliate Content Automation"
    )
    parser.add_argument(
        "--niche",
        choices=niche_choices,
        help=f"Target niche ({', '.join(niche_choices)})",
    )
    parser.add_argument(
        "--all-niches",
        action="store_true",
        help="Generate content for ALL niches",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="Products per niche (default: 3)",
    )
    parser.add_argument(
        "--trending",
        action="store_true",
        help="Use Google Trends data to find trending products",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Skip GitHub push (save files locally only)",
    )
    args = parser.parse_args()

    if not args.niche and not args.all_niches:
        parser.error("Specify --niche <name> or --all-niches")

    try:
        Config.validate(push_required=not args.no_push)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    niches_to_run = list(NICHES.keys()) if args.all_niches else [args.niche]

    for niche in niches_to_run:
        run_niche(
            niche=niche,
            count=args.count,
            push=not args.no_push,
            use_trends=args.trending,
        )


if __name__ == "__main__":
    main()
