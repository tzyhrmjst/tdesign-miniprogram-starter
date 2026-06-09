import unittest

from app.services.alert_service import _crossed_target


class AlertCrossingTest(unittest.TestCase):
    def test_above_alert_triggers_again_after_falling_back(self):
        prices = [695, 701, 705, 698, 703]
        expected = [False, True, False, False, True]
        triggered = False
        actual = []

        for index, current in enumerate(prices):
            previous = prices[index - 1] if index else None
            crossed = _crossed_target("above", 700, previous, current, triggered)
            actual.append(crossed)
            triggered = triggered or crossed

        self.assertEqual(actual, expected)

    def test_below_alert_triggers_again_after_rising_back(self):
        prices = [705, 699, 695, 702, 698]
        expected = [False, True, False, False, True]
        triggered = False
        actual = []

        for index, current in enumerate(prices):
            previous = prices[index - 1] if index else None
            crossed = _crossed_target("below", 700, previous, current, triggered)
            actual.append(crossed)
            triggered = triggered or crossed

        self.assertEqual(actual, expected)

    def test_new_rule_triggers_once_when_price_already_matches(self):
        self.assertTrue(_crossed_target("above", 700, None, 701, False))
        self.assertFalse(_crossed_target("above", 700, None, 701, True))


if __name__ == "__main__":
    unittest.main()
