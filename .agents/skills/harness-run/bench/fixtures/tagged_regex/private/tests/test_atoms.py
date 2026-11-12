import pytest
from .helpers import generated


@pytest.mark.parametrize("seed", range(10))
def test_atoms(seed):
    generated(seed, 'atoms')
