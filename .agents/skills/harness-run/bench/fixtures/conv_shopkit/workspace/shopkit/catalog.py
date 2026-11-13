def list_products(products, in_stock_only=False):
    out = []
    for p in products:
        if in_stock_only and p.get("stock", 0) <= 0:
            continue
        out.append(p)
    return sorted(out, key=lambda p: p["sku"])
