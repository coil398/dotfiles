from tomlkit.toml_document import TOMLDocument


def apply_edits(document, edits) -> TOMLDocument:
    """Apply the ordered batch described in docs/SPEC.md."""
    raise NotImplementedError("batch editing")
