import pytest
from ._checks import check


@pytest.mark.parametrize("seed", range(6))
def test_recursive_graphs(seed):
    check("recursive", seed)
