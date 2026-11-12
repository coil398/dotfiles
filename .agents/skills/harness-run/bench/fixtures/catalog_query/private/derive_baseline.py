# /// script
# dependencies = []
# ///
"""Derive the intentionally incomplete workspace from the reference."""
from pathlib import Path
import shutil
ROOT = Path(__file__).resolve().parents[1]
shutil.copytree(ROOT/'private/reference/catalog', ROOT/'workspace/catalog', dirs_exist_ok=True)

def change(file,before,after):
    path=ROOT/'workspace/catalog'/file
    text=path.read_text()
    assert text.count(before)==1
    path.write_text(text.replace(before,after))

# Typed literal conversion, missing-value handling, sorting, and ownership are
# unfinished in the starting catalog, independently of parser tokenization.
change('literals.py', "    lower = text.casefold()\n", "    return None if text.casefold() == 'null' else text\n    lower = text.casefold()\n")
# Remove dead conversion code from the starting implementation.
p=ROOT/'workspace/catalog/literals.py'
s=p.read_text(); p.write_text(s[:s.index('    lower = text.casefold()')])
change('matching.py', 'if left is MISSING:\n        return False', 'if left is MISSING:\n        left = None')
p=ROOT/'workspace/catalog/sorting.py'
s=p.read_text(); p.write_text(s[:s.index('def ordered(')] + 'def ordered(rows, fields):\n    return list(rows)\n')
change('storage.py', 'deepcopy([dict(record) for record in records])', '[dict(record) for record in records]')
change('pagination.py', 'type(offset) is not int', 'not isinstance(offset, int)')
