from boa3.builtin import public
from boa3.builtin.interop.blockchain.block import Block


@public
def main() -> Block:
    return Block()
