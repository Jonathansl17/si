import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from spring_init.errors import UnsafeArchiveError, ValidationError
from spring_init.extract import extract_zip

EXECUTABLE_MODE = 0o100755


def make_zip(entries: dict[str, bytes], executable: tuple[str, ...] = ()) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in entries.items():
            info = zipfile.ZipInfo(name)
            if name in executable:
                info.external_attr = EXECUTABLE_MODE << 16
            archive.writestr(info, content)
    return buffer.getvalue()


class ExtractTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_writes_nested_files(self):
        extract_zip(make_zip({"src/main/App.java": b"class App {}"}), self.target)
        self.assertEqual((self.target / "src/main/App.java").read_bytes(), b"class App {}")

    def test_keeps_executable_bit(self):
        extract_zip(make_zip({"mvnw": b"#!/bin/sh"}, executable=("mvnw",)), self.target)
        self.assertTrue((self.target / "mvnw").stat().st_mode & 0o100)

    def test_rejects_path_traversal(self):
        with self.assertRaises(UnsafeArchiveError):
            extract_zip(make_zip({"../evil": b"x"}), self.target)
        self.assertFalse((self.target.parent / "evil").exists())

    def test_refuses_to_overwrite_before_writing_anything(self):
        (self.target / "pom.xml").write_text("mine")
        archive = make_zip({"a.txt": b"new", "pom.xml": b"theirs"})
        with self.assertRaises(ValidationError):
            extract_zip(archive, self.target)
        self.assertEqual((self.target / "pom.xml").read_text(), "mine")
        self.assertFalse((self.target / "a.txt").exists())


if __name__ == "__main__":
    unittest.main()
