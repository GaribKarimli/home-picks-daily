import json, re
d = json.load(open("scripts/my_products.json", encoding="utf-8"))
for p in d["products"]:
    price = p.get("price", "")
    m = re.search(r"([\d.]+)", price.replace(",", ""))
    if m:
        val = float(m.group(1))
        usd = val / 1.7
        p["price"] = f"${usd:.2f}"
    elif not price or price == "?":
        p["price"] = ""
json.dump(d, open("scripts/my_products.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
for p in d["products"]:
    print(f"  {p['asin']}: {p['price']}")
