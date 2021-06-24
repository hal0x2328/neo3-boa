from boa3.builtin import public
from boa3.builtin.interop.binary import base58_check_decode


@public
def main(key: str) -> bytes:
    return base58_check_decode(key)