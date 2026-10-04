import unittest
from units import to_base_units, from_base_units

class TestUnits(unittest.TestCase):
    def test_smallest_unit(self):
        self.assertEqual(to_base_units("0.000001", 6), 1)

    def test_reject_too_many_decimals(self):
        with self.assertRaises(ValueError):
            to_base_units("1.1234567", 6)

    def test_reject_negative(self):
        with self.assertRaises(ValueError):
            to_base_units("-5", 6)

    def test_reject_scientific(self):
        with self.assertRaises(ValueError):
            to_base_units("1e3", 6)

    def test_reject_float_input(self):
        with self.assertRaises(ValueError):
            to_base_units(1.5, 6)

    def test_reject_empty_and_nan(self):
        for bad in ["", "nan", "inf", " 1", "1 "]:
            with self.assertRaises(ValueError):
                to_base_units(bad, 6)

    def test_trailing_dot(self):
        with self.assertRaises(ValueError):
            to_base_units("1.", 6)

    def test_zero(self):
        self.assertEqual(to_base_units("0", 6), 0)

    def test_big_number(self):
        self.assertEqual(to_base_units("20", 18), 20 * 10 ** 18)

    def test_from_base_units(self):
        self.assertEqual(from_base_units(1500000, 6), "1.5")
        self.assertEqual(from_base_units(1, 6), "0.000001")
        self.assertEqual(from_base_units(0, 6), "0")

    def test_reject_unicode_digits(self):
        with self.assertRaises(ValueError):
            to_base_units("１２３", 6)

    def test_no_precision_loss_big(self):
        self.assertEqual(
            to_base_units("123456789012.123456789012345678", 18),
            123456789012123456789012345678,
        )

    def test_big_roundtrip(self):
        s = "123456789012.123456789012345678"
        self.assertEqual(from_base_units(to_base_units(s, 18), 18), s)
if __name__ == "__main__":
    unittest.main()