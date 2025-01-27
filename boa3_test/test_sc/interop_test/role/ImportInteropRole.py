from boa3.builtin import interop, public
from boa3.builtin.type import ECPoint


@public
def main(role_: interop.role.Role, index: int) -> ECPoint:
    return interop.role.get_designated_by_role(role_, index)
