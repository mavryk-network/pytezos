from os.path import dirname
from os.path import join
from unittest import TestCase

from pytezos import ContractInterface
from pytezos import MichelsonRuntimeError


class NftContractTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nft = ContractInterface.from_file(join(dirname(__file__), 'contracts', 'nft.tz'))

    def test_mint(self):
        res = self.nft.mint(nftToMintId=42, nftToMint='mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN').interpret(storage={})
        self.assertDictEqual({42: 'mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN'}, res.storage)

    def test_mint_existing(self):
        res = self.nft.mint(nftToMintId=42, nftToMint='mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN').interpret(
            storage={42: 'mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN'}
        )
        self.assertDictEqual({42: 'mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN'}, res.storage)

    def test_transfer_skip(self):
        res = self.nft.transfer(nftToTransfer=42, destination='mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN').interpret(
            storage={42: 'mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN'}
        )
        self.assertDictEqual({42: 'mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN'}, res.storage)

    def test_transfer_non_existing(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.nft.transfer(nftToTransfer=42, destination='mv2LFe6Haxk32BC5xgEmK6QGocGqXdAtJDHT').interpret(
                storage={}, source='mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN'
            )

    def test_transfer_unwanted(self):
        res = self.nft.transfer(nftToTransfer=42, destination='mv2LFe6Haxk32BC5xgEmK6QGocGqXdAtJDHT').interpret(
            storage={42: 'mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN'}
        )
        self.assertDictEqual({42: 'mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN'}, res.storage)

    def test_transfer(self):
        res = self.nft.transfer(nftToTransfer=42, destination='mv2LFe6Haxk32BC5xgEmK6QGocGqXdAtJDHT').interpret(
            storage={42: 'mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN'}, source='mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN'
        )
        self.assertDictEqual({42: 'mv2LFe6Haxk32BC5xgEmK6QGocGqXdAtJDHT'}, res.storage)

    def test_burn_unwanted(self):
        res = self.nft.burn(42).interpret(storage={42: 'mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN'})
        self.assertDictEqual({42: 'mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN'}, res.storage)

    def test_burn_non_existing(self):
        with self.assertRaises(MichelsonRuntimeError):
            self.nft.burn(42).interpret(storage={})

    def test_burn(self):
        res = self.nft.burn(42).interpret(
            storage={42: 'mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN'}, source='mv1ShDp4Q4aFEcFwyhPkr7YZ8nd6cNbxntvN'
        )
        self.assertDictEqual({}, res.storage)
