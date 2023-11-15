import logging
from os import listdir
from os.path import dirname
from os.path import join
from unittest.case import TestCase

from pymavryk.logging import logger
from pymavryk.michelson.parse import MichelsonParser
from pymavryk.michelson.parse import michelson_to_micheline
from pymavryk.michelson.repl import Interpreter


class TztTest(TestCase):
    path = join(dirname(__file__), "tzt")
    exclude = [
        ".git",
        "LICENSE",
        # NOTE: unknown primitive `MumavOverflow`
        "add_mumav-mumav_01.tzt",
        # NOTE: unknown primitive `Contract`
        "address_00.tzt",
        "address_01.tzt",
        "address_02.tzt",
        "contract_00.tzt",
        "contract_01.tzt",
        "contract_02.tzt",
        "contract_03.tzt",
        "contract_04.tzt",
        "contract_05.tzt",
        # NOTE: failed to parse expression LexToken(_,'_',1,658)
        "createcontract_00.tzt",
        "createcontract_01.tzt",
        # NOTE: unknown primitive `Failed`
        "failwith_00.tzt",
        # NOTE: unknown primitive `GeneralOverflow`
        "lsl_01.tzt",
        # NOTE: unknown primitive `GeneralOverflow`
        "lsr_01.tzt",
        # NOTE: unknown primitive `MumavOverflow`
        "mul_mumav-nat_01.tzt",
        # NOTE: unknown primitive `MumavOverflow
        "mul_nat-mumav_01.tzt",
        # NOTE: parameter type is not defined
        "self_00.tzt",
        # NOTE: failed to parse expression LexToken(_,'_',1,199)
        "setdelegate_00.tzt",
        # NOTE: ('SLICE', 'string is empty')
        "slice_string_05.tzt",
        # NOTE: unknown primitive `MumavUnderflow`
        "sub_mumav-mumav_01.tzt",
        # NOTE: failed to parse expression LexToken(_,'_',1,238)
        "transfertokens_00.tzt",
        "transfertokens_01.tzt",
    ]

    def test_tzt(self) -> None:
        parser = MichelsonParser()
        for filename in listdir(self.path):
            if filename in self.exclude:
                continue
            with self.subTest(filename):
                filename = join(self.path, filename)
                with open(filename) as file:
                    script = michelson_to_micheline(
                        file.read(),
                        parser=parser,
                    )

                    Interpreter.run_tzt(script=script)
