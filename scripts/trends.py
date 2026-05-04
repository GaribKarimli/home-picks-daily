from pytrends.request import TrendReq

from scripts.config import NICHES


def get_trending_searches(niche: str | None = None, top_n: int = 5) -> list[tuple[str, int]]:
    """
    Fetch trending keywords from Google Trends for the past 7 days.

    Returns sorted list of (keyword, interest_score) tuples.
    Falls back to niche defaults if the API fails.
    """
    if niche:
        keywords = NICHES[niche]["trends_keywords"]
    else:
        keywords = []
        for n in NICHES.values():
            keywords.extend(n["trends_keywords"])

    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        results = {}

        for kw in keywords:
            try:
                pytrends.build_payload([kw], timeframe="now 7-d", geo="US")
                data = pytrends.interest_over_time()
                if not data.empty and kw in data.columns:
                    results[kw] = int(data[kw].iloc[-1])
            except Exception:
                continue

        if results:
            sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
            return sorted_results[:top_n]

    except Exception as e:
        print(f"  [WARN] Google Trends API failed: {e}")

    print("  [~] Trends API unavailable. Using default keywords.")
    return [(kw, 50) for kw in keywords[:top_n]]


def get_trending_search_terms(niche: str | None = None, top_n: int = 3) -> list[str]:
    """
    Get the best search terms for Amazon scraping based on trends.
    Returns Amazon-ready search query strings.
    """
    trends = get_trending_searches(niche, top_n)
    terms = []
    for kw, score in trends:
        term = kw.lower().replace(" ", "+")
        terms.append(term)
    return terms
