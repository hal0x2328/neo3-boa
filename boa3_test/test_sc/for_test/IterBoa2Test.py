from boa3.builtin import public


@public
def main() -> int:

    items = [1, 2, 4, 8]

    j = 3

    for i in items:
        j += i

    return j
