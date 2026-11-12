import pytest
from ._checks import check


@pytest.mark.parametrize("seed", range(6))
def test_sequential_graphs(seed):
    check("sequential", seed)
