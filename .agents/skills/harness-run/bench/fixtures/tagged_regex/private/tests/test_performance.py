import pytest
from .helpers import performance


@pytest.mark.parametrize("seed", range(10))
def test_performance(seed):
    performance(seed)
