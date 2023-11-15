import logging
from unittest import TestCase
from unittest import skip

from pymavryk import pymavryk

logging.basicConfig(level=logging.INFO)


class TestInjection(TestCase):
    @skip('not implemented')
    def test_one(self):
        counter = pymavryk.using('florencenet').contract('KT1ECSt8FzxAtHxoxi4xN1JwkKUbBe4TS9kz')
        res = counter.increment(1).send(min_confirmations=3)

    @skip('not implemented')
    def test_batch(self):
        operations = [pymavryk.transaction(destination=pymavryk.key.public_key_hash(), amount=1) for _ in range(41)]
        res = pymavryk.bulk(*operations).send(ttl=60, min_confirmations=1)
