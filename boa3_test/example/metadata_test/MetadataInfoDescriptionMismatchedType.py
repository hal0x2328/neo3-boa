from boa3.builtin import metadata, NeoMetadata


def Main() -> int:
    return 5


@metadata
def description_manifest() -> NeoMetadata:
    meta = NeoMetadata()
    meta.description = [0, 4, 8, 12]
    return meta
