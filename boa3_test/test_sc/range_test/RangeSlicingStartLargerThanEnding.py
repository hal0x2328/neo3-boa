from boa3.builtin import public


@public
def Main() -> range:
    a = range(6)
    return a[3:2]   # expect range(2, 3)
