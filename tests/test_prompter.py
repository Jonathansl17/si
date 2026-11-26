import unittest

from spring_init.errors import AbortedError, GoBack
from spring_init.metadata import Dependency
from spring_init.prompter import NONE_KEY, Prompter


class FakeFzf:
    def __init__(self, picked):
        self.picked = picked
        self.marked = None
        self.rows = None

    def search(self, prompt, rows, header, marked=()):
        self.rows, self.marked = rows, marked
        return self.picked


def reader(*answers):
    queue = list(answers)

    def read_line(prompt):
        answer = queue.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return answer
    return read_line


def dep(dep_id):
    return Dependency(dep_id, dep_id.title(), "", "Web", None)


class TextTest(unittest.TestCase):
    def test_empty_answer_keeps_default(self):
        self.assertEqual(Prompter(None, reader("")).text("Group", "com.example"), "com.example")

    def test_answer_replaces_default(self):
        self.assertEqual(Prompter(None, reader(" io.acme ")).text("Group", "x"), "io.acme")

    def test_q_goes_back(self):
        with self.assertRaises(GoBack):
            Prompter(None, reader("q")).text("Group", "com.example")

    def test_ctrl_d_aborts(self):
        with self.assertRaises(AbortedError):
            Prompter(None, reader(EOFError())).text("Group", "com.example")


class ConfirmTest(unittest.TestCase):
    def test_enter_confirms_and_n_declines(self):
        self.assertTrue(Prompter(None, reader("")).confirm(""))
        self.assertFalse(Prompter(None, reader("n")).confirm(""))

    def test_q_goes_back(self):
        with self.assertRaises(GoBack):
            Prompter(None, reader("q")).confirm("")


class DependenciesTest(unittest.TestCase):
    def test_none_row_is_dropped_from_result(self):
        fzf = FakeFzf([NONE_KEY])
        self.assertEqual(Prompter(fzf, None).dependencies([dep("web")], []), [])

    def test_back_drops_none_row_from_kept_marks(self):
        class BackFzf(FakeFzf):
            def search(self, prompt, rows, header, marked=()):
                raise GoBack([NONE_KEY, "web"])

        with self.assertRaises(GoBack) as raised:
            Prompter(BackFzf([]), None).dependencies([dep("web")], [])
        self.assertEqual(raised.exception.kept, ["web"])

    def test_previous_choices_start_marked(self):
        fzf = FakeFzf(["web"])
        Prompter(fzf, None).dependencies([dep("lombok"), dep("web")], ["web"])
        self.assertEqual([fzf.rows[i].key for i in fzf.marked], ["web"])


if __name__ == "__main__":
    unittest.main()
