import os
os.environ["DATABASE_URL"] = "sqlite://"      # 必須在 import app 之前

import unittest
from sqlalchemy.exc import IntegrityError, StatementError
from app import app, db, Token, Pool, PoolReserve, Swap


class ModelTestCase(unittest.TestCase):
    def setUp(self):
        # 保險：絕對不能對真正的 swap.db 做 drop_all
        self.assertEqual(app.config["SQLALCHEMY_DATABASE_URI"], "sqlite://")
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()
        db.session.add_all([Token(symbol="USDT", decimals=6),
                            Token(symbol="ETH", decimals=18)])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def make_pool(self):
        pool = Pool(token_a="ETH", token_b="USDT", last_updated_time="t")
        db.session.add(pool)
        db.session.commit()
        return pool


class TestForeignKey(ModelTestCase):
    def test_reserve_with_unknown_token_rejected(self):
        pool = self.make_pool()
        db.session.add(PoolReserve(pool_id=pool.id, token="DOGE", reserve=1))
        with self.assertRaises(IntegrityError):
            db.session.commit()
    def test_swap_with_unknown_token_rejected(self):
        new_swap = Swap(
            token_in="SUI",
            token_out="USDT",
            amount_in=100,
            amount_out=1,
            created_at="t"
        )
        db.session.add(new_swap)
        with self.assertRaises(IntegrityError):
            db.session.commit()
    def test_swap_with_unknown_token_out_rejected(self):
        new_swap = Swap(
            token_in="USDT",
            token_out="SUI",
            amount_in=100,
            amount_out=1,
            created_at="t"
        )
        db.session.add(new_swap)
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_pool_with_unknown_token_rejected(self):
        db.session.add(Pool(token_a="SUI", token_b="USDT", last_updated_time="t"))
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_pool_with_unknown_token_out_rejected(self):
        db.session.add(Pool(token_a="USDT", token_b="SUI", last_updated_time="t"))
        with self.assertRaises(IntegrityError):
            db.session.commit()

class TestConstraints(ModelTestCase):
    def test_duplicate_pair_rejected(self):
        pool1 = self.make_pool()
        new_pool = Pool(
            token_a="ETH",
            token_b="USDT",
            last_updated_time="t"
        )
        db.session.add(new_pool)
        with self.assertRaises(IntegrityError): # 期望下一步會拋 IntegrityError 例外，如果沒拋就測試失敗。
            db.session.commit()

    def test_token_requires_decimals(self):
        db.session.add(Token(symbol="ZEC", decimals=None))
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_reserve_none_rejected(self):
        pool = self.make_pool()
        db.session.add(PoolReserve(pool_id=pool.id, token="ETH", reserve=None))
        with self.assertRaises(IntegrityError):
            db.session.commit()

class TestBigIntColumn(ModelTestCase):
    def test_big_value_roundtrip(self):
        pool = self.make_pool()
        big = 123456789012123456789012345678      # 遠超過 SQLite INTEGER 上限
        db.session.add(PoolReserve(pool_id=pool.id, token="ETH", reserve=big))
        db.session.commit()
        db.session.expire_all()
        row = PoolReserve.query.filter_by(token="ETH").one()
        self.assertEqual(row.reserve, big)
        self.assertIs(type(row.reserve), int)

    def test_float_reserve_rejected(self):
        pool = self.make_pool()
        db.session.add(PoolReserve(pool_id=pool.id, token="ETH", reserve=1.5))
        with self.assertRaises(StatementError) as cm:   # TypeError 會被包起來
            db.session.commit() #SQLAlchemy 會呼叫 BigIntAsText.process_bind_param() 試著轉換 1.5。
        self.assertIsInstance(cm.exception.orig, TypeError)

if __name__ == "__main__":
    unittest.main()