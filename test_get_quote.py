from test_case import QuoteTestCase # 必須最先 import：它會在 import app 之前設定 DATABASE_URL
import unittest
class TestTwoSideInput(QuoteTestCase):
    def test_normal_input(self):
        response = self.client.get('/quote?tokenIn=ETH&tokenOut=USDT&amountIn=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "tokenIn": "ETH",
                "tokenOut": "USDT",
                "amountIn": "1",
                "amountOut": "2272.727272"
            })
    def test_reverse_input(self):
        response = self.client.get('/quote?tokenIn=USDT&tokenOut=ETH&amountIn=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "tokenIn": "USDT",
                "tokenOut": "ETH",
                "amountIn": "1",
                "amountOut": "0.000399984000639974"
            })
class TestInvalidInputError(QuoteTestCase):
    def test_same_input_token(self):
        response = self.client.get('/quote?tokenIn=ETH&tokenOut=ETH&amountIn=1')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)
    def test_input_empty_amountIn(self):
        response = self.client.get('/quote?tokenIn=ETH&tokenOut=USDT&amountIn=')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)
    def test_input_without_amountIn(self):
        response = self.client.get('/quote?tokenIn=ETH&tokenOut=USDT')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)
    def test_input_without_tokenIn(self):
        response = self.client.get('/quote?tokenOut=USDT&amountIn=1')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)
class TestNoResourceError(QuoteTestCase):
    def test_not_exist_token(self):
        response = self.client.get('/quote?tokenIn=ZEC&tokenOut=USDT&amountIn=1')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json)
class TestUnexpectedError(QuoteTestCase):
    def test_unexpected_error_returns_500(self):
        from unittest import mock
        with mock.patch('routes.quote', side_effect=TypeError("Mock TypeError")):
            response = self.client.get('/quote?tokenIn=ETH&tokenOut=USDT&amountIn=1')
        self.assertEqual(response.status_code, 500)
if __name__ == "__main__":
    unittest.main()