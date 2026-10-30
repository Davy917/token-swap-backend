from units import to_base_units
import os
# 記憶體資料庫，完全獨立
os.environ["DATABASE_URL"] = "sqlite://"      # 必須在 import app 之前

import unittest
from services import quote, InvalidInputError, NoResourceError, QuoteResult
from app import app, db, Token, Pool, PoolReserve

class QuoteTestCase(unittest.TestCase):
    def setUp(self):
        # 保險：絕對不能對真正的 swap.db 做 drop_all
        self.assertEqual(app.config["SQLALCHEMY_DATABASE_URI"], "sqlite://") # （沒有檔案路徑）代表純記憶體資料庫，程式一結束就消失，跟 swap.db 完全無關。
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()
        db.session.add_all([Token(symbol="USDT", decimals=6),
                            Token(symbol="ETH", decimals=18),
                            Token(symbol="BTC", decimals=8)
                           ])
        db.session.commit()
        new_pool = Pool(token_a="ETH", token_b="USDT", last_updated_time="t")
        db.session.add(new_pool)
        db.session.flush()
        pool_id = new_pool.id
        usdt_reserve = PoolReserve(
            pool_id=pool_id,
            token="USDT",
            reserve=to_base_units("25000", 6)
        )
        eth_reserve = PoolReserve(
            pool_id=pool_id,
            token="ETH",
            reserve=to_base_units("10", 18)
        )
        db.session.add_all([usdt_reserve, eth_reserve])
        db.session.commit()


    def tearDown(self): # 每次清空
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

class TestTwoSideInput(QuoteTestCase):
    def test_normal_input(self):
        result = quote("ETH", "USDT", "1")
        self.assertEqual(
            result,
            QuoteResult(
                token_in="ETH",
                token_out="USDT",
                amount_in=10**18,
                amount_out=2272727272,
                decimals_in=18,
                decimals_out=6
            )
        )
    def test_reverse_input(self):
        result = quote("USDT", "ETH", "1")
        self.assertEqual(
            result,
            QuoteResult(
                token_in="USDT",
                token_out="ETH",
                amount_in=10**6,
                amount_out=399984000639974,
                decimals_in=6,
                decimals_out=18
            )
        )
class TestNormalizeInput(QuoteTestCase):
    def test_input_with_space_and_lower_case(self):
        result = quote(" eth ", "usdt", "1")
        self.assertEqual(
            result,
            QuoteResult(
                token_in="ETH",
                token_out="USDT",
                amount_in=10**18,
                amount_out=2272727272,
                decimals_in=18,
                decimals_out=6
            )
        )
class TestInvalidInputError(QuoteTestCase):
    def test_same_input_token(self):
        with self.assertRaises(InvalidInputError):
            quote("ETH", "ETH", "1")
    def test_tiny_input_amount(self):
        with self.assertRaises(InvalidInputError):
            quote("ETH", "USDT", "0.000000000000000001")  # 1 wei ETH，換到 0 → InvalidInputError
    def test_invalid_amount_input(self):
        invalid_amounts = ["1.5.5", "abc", "0", "-1"]
        for amount in invalid_amounts:
            with self.subTest(amount=amount):
                with self.assertRaises(InvalidInputError):
                    quote("ETH", "USDT", amount)
    def test_too_many_decimals_for_token_in(self):
        with self.assertRaises(InvalidInputError):
            quote("USDT", "ETH", "0.0000001")

    def test_eth_accepts_many_decimals(self):
        result = quote("ETH", "USDT", "0.0000001")
        self.assertEqual(result.amount_in, 10 ** 11)
    """
    quote("USDT", "ETH", "0.0000001") → USDT 的 decimals=6，但輸入 7 位小數 → InvalidInputError ✅
    quote("ETH", "USDT", "0.0000001") → ETH 的 decimals=18，輸入 7 位小數在範圍內 → 成功 ✅
    這樣確保 quote() 的實作裡，用 token_in 的 decimals 去驗證 amount_in，而不是用 token_out 的。
    """
class TestNoResourceError(QuoteTestCase):
    def test_input_not_exist_token(self):
        with self.assertRaises(NoResourceError):
            quote("ZEC", "USDT", "10")
        with self.assertRaises(NoResourceError):
            quote("ETH", "ZEC", "10")
    def test_input_not_exist_pool(self):
        with self.assertRaises(NoResourceError):
            quote("BTC", "USDT", "0.5")
        with self.assertRaises(NoResourceError):
            quote("USDT", "BTC", "0.5")
class TestReserveChangeOrNot(QuoteTestCase):
    def test_reserve_no_change_after_quote(self):
        before_eth_reserve = PoolReserve.query.filter_by(token="ETH").one().reserve
        before_usdt_reserve = PoolReserve.query.filter_by(token="USDT").one().reserve
        quote("ETH", "USDT", "1")
        after_eth_reserve = PoolReserve.query.filter_by(token="ETH").one().reserve
        after_usdt_reserve = PoolReserve.query.filter_by(token="USDT").one().reserve
        self.assertEqual(before_eth_reserve, after_eth_reserve, "檢測失敗, ETH reserve有改動")
        self.assertEqual(before_usdt_reserve, after_usdt_reserve, "檢測失敗, USDT reserve有改動")

class TestErrorMsgSequence(QuoteTestCase):
    def test_same_token_and_not_exist_error_msg_order(self):
        with self.assertRaises(InvalidInputError):
            quote("SUI", "SUI", "10")

if __name__ == "__main__":
    unittest.main()