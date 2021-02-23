from typing import Dict

from boa3.builtin import public


@public
def main(value: int, some_dict: Dict[int, str]) -> bool:
    return value not in some_dict
