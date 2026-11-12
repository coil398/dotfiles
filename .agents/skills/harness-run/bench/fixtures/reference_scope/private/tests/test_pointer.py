import pytest
from ._checks import check


@pytest.mark.parametrize("seed", range(6))
def test_pointer_graphs(seed):
    check("pointer", seed)
