from test_case import QuoteTestCase # 必須最先 import：它會在 import app 之前設定 DATABASE_URL
from services import quote, InvalidInputError, NoResourceError, QuoteResult
from app import PoolReserve
import unittest

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

class TestTypeErrorPropagation(QuoteTestCase):
    def test_get_amount_out_type_error_propagates(self):
        from unittest import mock
        with mock.patch('services.get_amount_out', side_effect=TypeError("Mock TypeError")): # 1. 布置：把函式換成假的
            with self.assertRaises(TypeError) as ctx:                                        # 2. 準備：等著接 TypeError
                quote("ETH", "USDT", "1")                         # 3. 執行：真的跑 quote()
            self.assertEqual(str(ctx.exception), "Mock TypeError")                    # 4. 檢查

if __name__ == "__main__":
    unittest.main()