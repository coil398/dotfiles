"""The policy language intentionally preserves Python exception classes."""

def syntax(message):
    raise SyntaxError(message)
