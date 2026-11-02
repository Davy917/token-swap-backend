from test_case import ModelTestCase  # 必須最先 import：它會在 import app 之前設定 DATABASE_URL
from sqlalchemy.exc import IntegrityError, StatementError
from app import db, Token, Pool, PoolReserve, Swap
import unittest

class TestForeignKey(ModelTestCase):
    def test_reserve_with_unknown_token_rejected(self):
        pool = self.make_pool()
        db.session.add(PoolReserve(pool_id=pool.id, token="DOGE", reserve=1))
        with self.assertRaises(IntegrityError): # 期望下一步會拋 IntegrityError 例外，如果沒拋就測試失敗。
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
        self.make_pool()  # 先建立 (ETH, USDT)
        new_pool = Pool(
            token_a="ETH",
            token_b="USDT",
            last_updated_time="t"
        )
        db.session.add(new_pool)
        with self.assertRaises(IntegrityError):
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

    def test_reversed_pair_rejected(self):
        db.session.add(Pool(token_a="USDT", token_b="ETH", last_updated_time="t"))
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_same_token_pair_rejected(self):
        db.session.add(Pool(token_a="ETH", token_b="ETH", last_updated_time="t"))
        with self.assertRaises(IntegrityError):
            db.session.commit()

class TestFlushRollback(ModelTestCase):
    def test_flush_then_bad_reserve_rolls_back_pool(self):
        # 1. 建立 Pool 並 flush（讓資料庫產生 id，但尚未 commit）
        pool = Pool(token_a="ETH", token_b="USDT", last_updated_time="t")
        db.session.add(pool)
        db.session.flush()

        # 2. 加一筆 token="DOGE"（不存在於 tokens 表），commit 應該拋 IntegrityError
        db.session.add(PoolReserve(pool_id=pool.id, token="DOGE", reserve=1))
        with self.assertRaises(IntegrityError):
            db.session.commit()

        # 3. rollback 之後，Pool 也應該一起消失
        db.session.rollback()
        self.assertEqual(Pool.query.count(), 0)

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