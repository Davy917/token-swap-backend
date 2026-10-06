import random
import unittest
from amm import get_amount_out
class TestAmm(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(get_amount_out(2, 50, 1), 16)
    def test_float_precision_regression(self):
        with self.assertRaises(ValueError):
            get_amount_out(10 ** 20 + 1, 2, 10 ** 20)
    def test_zero_amount_in_raises(self):
        with self.assertRaises(ValueError):
            get_amount_out(100, 50, 0)
    def test_type_check(self):
        with self.assertRaises(TypeError):
            get_amount_out(100, 50, 1.5)
        with self.assertRaises(TypeError):
            get_amount_out(100, 50, "100")
        with self.assertRaises(TypeError):
            get_amount_out(100, 50, True)
        with self.assertRaises(TypeError):
            get_amount_out(100, 0.5, 1)
    def test_edge_number(self):
        with self.assertRaises(ValueError):
            get_amount_out(100, 50, -1)
        with self.assertRaises(ValueError):
            get_amount_out(0, 50, 1)
        with self.assertRaises(ValueError):
            get_amount_out(100, 0, 1)
        with self.assertRaises(ValueError):
            get_amount_out(100, 1, 10**6)

class TestInvariant(unittest.TestCase):
    def test_k_never_decreases(self):
        rng = random.Random(42)          # 固定種子，失敗時可以重現
        checked = 0
        for _ in range(20000):
            digits = rng.choice([1, 3, 6, 12, 18])   # 不同量級都要測
            reserve_in = rng.randint(1, 10 ** digits)
            reserve_out = rng.randint(1, 10 ** digits)
            amount_in = rng.randint(1, 10 ** digits)
            try:
                amount_out = get_amount_out(reserve_in, reserve_out, amount_in)
            except ValueError:
                continue                 # amount_out 為 0 被拒絕，不檢查
            checked += 1
            k_before = reserve_in * reserve_out
            k_after = (reserve_in + amount_in) * (reserve_out - amount_out)
            self.assertGreaterEqual(
                k_after, k_before,
                f"k 變小了: rin={reserve_in}, rout={reserve_out}, ain={amount_in}, out={amount_out}")
            self.assertLess(amount_out, reserve_out)   # 池子不會被抽乾
        self.assertGreater(checked, 1000)  # 防止全被拒絕、測試空轉
if __name__ == "__main__":
    unittest.main()