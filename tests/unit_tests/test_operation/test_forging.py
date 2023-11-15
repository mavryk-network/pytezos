import json
from os.path import dirname
from os.path import join
from unittest import TestCase

from parameterized import parameterized  # type: ignore

from pymavryk import pymavryk
from pymavryk.operation.group import OperationGroup


class TestOperationForging(TestCase):
    @parameterized.expand(
        [
            ("ooDVUV9EKeSWntCt56qgjtrHkLxRoHnTcqVVdaPTLvXQiY8xT4u",),
            ("opJfNSFsfjW26kpuyVByAF2Ha3avghrYS4u11uSFpjr8ZUsoHbs",),
            ("ooYuPSt5UNe3unMmBsM55JgHzMBsJAMxyebw9vTbaC6YWtxcdQ3",),
        ]
    )
    def test_operation_hash_is_correct(self, opg_hash):
        with open(join(dirname(__file__), 'data', f'{opg_hash}.json')) as f:
            data = json.loads(f.read())

        group = OperationGroup(
            context=pymavryk.using('mumbainet').context,
            contents=data['contents'],
            chain_id=data['chain_id'],
            protocol=data['protocol'],
            branch=data['branch'],
            signature=data['signature'],
        )
        res = group.hash()
        self.assertEqual(opg_hash, res)
