import pytest
from ._checks import check


@pytest.mark.parametrize("seed", range(6))
def test_base_uri_graphs(seed):
    check("base_uri", seed)
