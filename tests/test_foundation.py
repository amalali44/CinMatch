import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from recsys.cli import main
from recsys.data import profile_ratings

HEADER = "userId,movieId,rating,timestamp\n"


class DataContractTests(unittest.TestCase):
    def test_profile_known_values(self):
        result = profile_ratings(io.StringIO(HEADER + "1,2,4,100\n2,3,2,200\n"))
        self.assertEqual(result["interactions"], 2)
        self.assertEqual(result["rating"], {"min": 2, "max": 4, "mean": 3})
        self.assertEqual(result["timestamp"], {"min": 100, "max": 200})

    def test_rejects_invalid_values_with_line_number(self):
        rows = ["0,1,4,10", "2147483648,1,4,10", "1,-1,4,10",
                "1,1,nan,10", "1,1,inf,10", "1,1,5.5,10", "1,1,0,10",
                "1,1,3.7,10", "1,1,4,-1", "1,1,4,9223372036854775808",
                "1,1,4,nope", "1,1,4", "1.5,1,4,10"]
        for row in rows:
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, "line 2"):
                profile_ratings(io.StringIO(HEADER + row + "\n"))

    def test_requires_columns(self):
        with self.assertRaisesRegex(ValueError, "missing required columns"):
            profile_ratings(io.StringIO("userId,rating\n1,4\n"))

    def test_rejects_duplicate_headers(self):
        with self.assertRaisesRegex(ValueError, "duplicate column"):
            profile_ratings(io.StringIO(HEADER.strip() + ",rating\n"))

    def test_rejects_empty_dataset(self):
        with self.assertRaisesRegex(ValueError, "no rating records"):
            profile_ratings(io.StringIO(HEADER))

    def test_rejects_extra_values(self):
        with self.assertRaisesRegex(ValueError, "Extra CSV values at line 2"):
            profile_ratings(io.StringIO(HEADER + "1,2,4,100,extra\n"))

    def test_accepts_named_extra_columns(self):
        result = profile_ratings(io.StringIO(HEADER.strip() + ",tag\n1,2,4,100,test\n"))
        self.assertEqual(result["interactions"], 1)

    def test_rejects_malformed_csv(self):
        with self.assertRaisesRegex(ValueError, "Malformed CSV"):
            profile_ratings(io.StringIO(HEADER + '1,2,4,"unterminated'))


class CommandTests(unittest.TestCase):
    def test_sample_is_reproducible_and_labeled(self):
        outputs = []
        for _ in range(2):
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["profile", "--sample"]), 0)
            outputs.append(json.loads(output.getvalue()))
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0]["interactions"], 12)
        self.assertEqual(outputs[0]["source"], "bundled-synthetic-sample")

    def test_writes_json_and_creates_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "nested" / "profile.json"
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["profile", "--sample", "--output", str(target)]), 0)
            self.assertEqual(json.loads(target.read_text()), json.loads(output.getvalue()))

    def test_missing_file_returns_clean_error(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = str(Path(directory) / "absent.csv")
            with redirect_stderr(io.StringIO()) as error:
                self.assertEqual(main(["profile", "--ratings", missing]), 2)
            self.assertIn("recsys:", error.getvalue())

    def test_does_not_overwrite_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "ratings.csv"
            original = HEADER + "1,1,4,100\n"
            source.write_text(original)
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main(["profile", "--ratings", str(source),
                                       "--output", str(source)]), 2)
            self.assertEqual(source.read_text(), original)

    def test_reads_utf8_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "ratings.csv"
            source.write_text(HEADER + "1,1,4,100\n", encoding="utf-8-sig")
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["profile", "--ratings", str(source)]), 0)
            self.assertEqual(json.loads(output.getvalue())["interactions"], 1)


if __name__ == "__main__":
    unittest.main()
