from boa3.builtin import public


@public
def Main() -> str:
    a = 'unit_test'
    return a[:]   # expect 'unit_test'
