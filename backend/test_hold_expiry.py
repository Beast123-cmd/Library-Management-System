from datetime import timedelta
import unittest

from app.core.holds import HOLD_DURATION


class HoldExpiryTests(unittest.TestCase):
    def test_hold_duration_is_twelve_hours(self):
        self.assertEqual(HOLD_DURATION, timedelta(hours=12))


if __name__ == "__main__":
    unittest.main()
