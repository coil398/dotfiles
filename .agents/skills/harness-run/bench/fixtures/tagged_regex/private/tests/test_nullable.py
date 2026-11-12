import pytest
from .helpers import generated


@pytest.mark.parametrize("seed", range(10))
def test_nullable(seed):
    generated(seed, 'nullable')
