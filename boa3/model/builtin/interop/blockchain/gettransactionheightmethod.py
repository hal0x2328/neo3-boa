from typing import Dict

from boa3.model.builtin.interop.blockchain.transactiontype import TransactionType
from boa3.model.builtin.interop.nativecontract import LedgerMethod
from boa3.model.variable import Variable


class GetTransactionHeightMethod(LedgerMethod):

    def __init__(self):
        from boa3.model.type.collection.sequence.uint256type import UInt256Type
        from boa3.model.type.type import Type

        identifier = 'get_transaction_height'
        syscall = 'getTransactionHeight'
        args: Dict[str, Variable] = {'hash_': Variable(UInt256Type.build())}
        super().__init__(identifier, syscall, args, return_type=Type.int)