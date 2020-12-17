import base64
from typing import Any, Dict, List, Optional

from boa3.neo import from_hex_str, to_hex_str
from boa3.neo.core.types.UInt import UInt256
from boa3_test.tests.test_classes.signer import Signer
from boa3_test.tests.test_classes.witness import Witness


class Transaction:
    def __init__(self, script: bytes, signers: List[Signer] = None, witnesses: List[Witness] = None):
        self._signers: List[Signer] = signers if signers is not None else []
        self._witnesses: List[Witness] = witnesses if witnesses is not None else []
        self._script: bytes = script
        self._hash: Optional[UInt256] = None

    def to_json(self) -> Dict[str, Any]:
        return {
            'signers': [signer.to_json() for signer in self._signers],
            'witnesses': [witness.to_json() for witness in self._witnesses],
            'script': to_hex_str(self._script)
        }

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        script = base64.b64decode(json['script'])
        tx = cls(script)
        if 'signers' in json:
            signers_json = json['signers']
            if not isinstance(signers_json, list):
                signers_json = [signers_json]
            tx._signers = [Signer.from_json(js) for js in signers_json]

        if 'witnesses' in json:
            witnesses_json = json['witnesses']
            if not isinstance(witnesses_json, list):
                witnesses_json = [witnesses_json]
            tx._witnesses = [Witness.from_json(js) for js in witnesses_json]

        if 'hash' in json and isinstance(json['hash'], str):
            tx._hash = UInt256(from_hex_str(json['hash']))
        return tx

    def copy(self):
        copied = Transaction(self._script, self._signers, self._witnesses)
        copied._hash = self._hash
        return copied

    def get_hash(self):
        return self._hash
