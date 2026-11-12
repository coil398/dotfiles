import pytest
from ._checks import check


@pytest.mark.parametrize("seed", range(6))
def test_dynamic_graphs(seed):
    check("dynamic", seed)
