from boa3.builtin import public


@public
def Main() -> int:
    a = 0
    sequence = (3, 5, 15)

    for x in sequence:
        if x % 5 == 0:
            a += x
            break

        a += 1
    else:
        a = -1

    return a
