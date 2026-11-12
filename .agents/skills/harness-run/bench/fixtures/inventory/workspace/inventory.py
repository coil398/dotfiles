from dataclasses import dataclass, field


@dataclass
class Item:
    sku: str
    qty: int
    price_cents: int


@dataclass
class Inventory:
    items: dict = field(default_factory=dict)

    def add(self, sku, qty, price_cents):
        if sku in self.items:
            self.items[sku].qty = qty
        else:
            self.items[sku] = Item(sku, qty, price_cents)

    def remove(self, sku, qty):
        item = self.items[sku]
        item.qty -= qty
        if item.qty < 0:
            del self.items[sku]

    def total_value_cents(self):
        return sum(i.qty * i.price_cents for i in self.items.values())

    def low_stock(self, threshold):
        return [i.sku for i in self.items.values() if i.qty < threshold]
