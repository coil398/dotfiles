import subprocess
import sys
import pytest


@pytest.mark.parametrize('case', range(6))
def test_search_envelope(case):
    try:
        result = subprocess.run(
            [sys.executable, '-c',
             f'from tests_hidden.support import workload; workload({case})'],
            capture_output=True, text=True, timeout=8)
    except subprocess.TimeoutExpired:
        pytest.fail('search timed out (TimeoutExpired): SPEC section 6, 8-second family deadline')
    assert result.returncode == 0, result.stderr[-3000:]
