import pytest
from inventory import Inventory


def test_add_accumulates():
    inv = Inventory()
    inv.add("a", 2, 100)
    inv.add("a", 3, 100)
    assert inv.items["a"].qty == 5


def test_remove_to_zero_deletes():
    inv = Inventory()
    inv.add("a", 2, 100)
    inv.remove("a", 2)
    assert "a" not in inv.items


def test_remove_more_than_stock_raises():
    inv = Inventory()
    inv.add("a", 2, 100)
    with pytest.raises(ValueError):
        inv.remove("a", 3)
    assert inv.items["a"].qty == 2


def test_low_stock_inclusive_sorted():
    inv = Inventory()
    inv.add("b", 1, 1)
    inv.add("a", 5, 1)
    inv.add("c", 9, 1)
    assert inv.low_stock(5) == ["a", "b"]


def test_total():
    inv = Inventory()
    inv.add("a", 2, 150)
    inv.add("b", 1, 99)
    assert inv.total_value_cents() == 399
