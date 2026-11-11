Repository: the current working directory (a tiny Python project).
Goal: make all tests in test_inventory.py pass by fixing inventory.py only. Do not edit the tests.
Requirements implied by tests: add() accumulates qty for existing sku; remove() deletes the sku when qty reaches exactly 0; removing more than in stock raises ValueError and leaves stock unchanged; low_stock(threshold) is inclusive (qty <= threshold) and returns skus sorted.
Run `uv run -q --no-project --with pytest python -m pytest -q` to confirm. Do not commit.
Return: changed files, the test command result, and anything unverified.
