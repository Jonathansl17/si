import unittest

from spring_init import config
from spring_init.fzf import _marked_keys

SEP = config.FZF_FIELD_SEPARATOR


class MarkedKeysTest(unittest.TestCase):
    def test_menu_back_carries_nothing(self):
        self.assertIsNone(_marked_keys([config.BACK_SENTINEL]))

    def test_no_marks_ignores_row_under_cursor(self):
        lines = [f"{config.BACK_SENTINEL}0", f"web{SEP}web{SEP}Spring Web"]
        self.assertEqual(_marked_keys(lines), [])

    def test_marked_rows_are_kept(self):
        lines = [f"{config.BACK_SENTINEL}2", f"web{SEP}x", f"lombok{SEP}y"]
        self.assertEqual(_marked_keys(lines), ["web", "lombok"])


if __name__ == "__main__":
    unittest.main()
