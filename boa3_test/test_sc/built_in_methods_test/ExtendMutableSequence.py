from typing import MutableSequence


def Main(op: str, args: list) -> MutableSequence[int]:
    a: MutableSequence[int] = [1, 2, 3]
    a.extend([4, 5, 6])
    return a