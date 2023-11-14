from unittest import TestCase

from pytezos import pytezos


class CallbackViewTestCase(TestCase):
    def test_balance_of(self):
        usds = pytezos.using('mainnet').contract('KT1REEb5VxWRjcHm5GzDMwErMmNFftsE5Gpf')
        res = usds.balance_of(
            requests=[
                {'owner': 'mv1N913itbcFVECQPzKLzXfgN8jgZ6MaEPwE', 'token_id': 0},
                {'owner': 'mv19bzdiWWzVhwLHCCbPjeyLjiUMgdKAxsbF', 'token_id': 0},
                {'owner': 'mv2e9VsSX7VxigA4Z9eqMiEtQZdvnS7Go4j4', 'token_id': 0},
            ],
            callback=None,
        ).callback_view()
        print(res)

    def test_initial_storage(self):
        usds = pytezos.using('mainnet').contract('KT1REEb5VxWRjcHm5GzDMwErMmNFftsE5Gpf')
        storage = usds.storage()
        storage['ledger'] = {'mv1N913itbcFVECQPzKLzXfgN8jgZ6MaEPwE': 42}
        res = usds.balance_of(
            requests=[
                {'owner': 'mv1N913itbcFVECQPzKLzXfgN8jgZ6MaEPwE', 'token_id': 0},
            ],
            callback=None,
        ).callback_view(storage=storage)
        self.assertEqual(42, res[0]['balance'])

    def test_onchain_view(self):
        ci = pytezos.using('mainnet').contract('KT1F6Amndd62P8yySM5NkyF4b1Kz27Ft4QeT')
        res = ci.get_price().run_view()
        print(res)
