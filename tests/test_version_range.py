import unittest

from spring_init.errors import ValidationError
from spring_init.version_range import is_compatible, parse_version


class ParseVersionTest(unittest.TestCase):
    def test_qualifiers_order_like_initializr(self):
        ordered = ["4.3.0-M1", "4.3.0-RC1", "4.3.0-SNAPSHOT", "4.3.0"]
        self.assertEqual(sorted(ordered, key=parse_version), ordered)

    def test_legacy_release_suffix_equals_plain(self):
        self.assertEqual(parse_version("2.7.0.RELEASE"), parse_version("2.7.0"))

    def test_build_snapshot_is_parsed(self):
        self.assertEqual(parse_version("2.0.0.BUILD-SNAPSHOT"), parse_version("2.0.0-SNAPSHOT"))

    def test_rejects_garbage(self):
        with self.assertRaises(ValidationError):
            parse_version("latest")


class RangeTest(unittest.TestCase):
    def test_no_range_is_always_compatible(self):
        self.assertTrue(is_compatible(None, "4.2.0"))

    def test_bare_version_is_lower_bound(self):
        self.assertTrue(is_compatible("4.0.0", "4.2.0"))
        self.assertFalse(is_compatible("4.0.0", "3.5.0"))

    def test_exclusive_upper_bound_rejects_milestone(self):
        self.assertTrue(is_compatible("[4.0.0,4.3.0-M1)", "4.2.1-SNAPSHOT"))
        self.assertFalse(is_compatible("[4.0.0,4.3.0-M1)", "4.3.0-M1"))

    def test_inclusive_upper_and_exclusive_lower(self):
        self.assertTrue(is_compatible("(3.0.0,3.5.0]", "3.5.0"))
        self.assertFalse(is_compatible("(3.0.0,3.5.0]", "3.0.0"))

    def test_malformed_range_raises(self):
        with self.assertRaises(ValidationError):
            is_compatible("[4.0.0", "4.2.0")


if __name__ == "__main__":
    unittest.main()
