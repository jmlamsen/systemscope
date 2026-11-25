import unittest

from monitor import capacity


class WarningTests(unittest.TestCase):
    def test_memory_cutoff(self):
        self.assertEqual(capacity(1.8, 12)[0], "OK")
        self.assertEqual(capacity(1.79, 12)[0], "Low")

    def test_target_drive(self):
        self.assertEqual(capacity(14, 117)[0], "Low")

    def test_missing_drive(self):
        self.assertEqual(capacity(None, None)[0], "Unavailable")