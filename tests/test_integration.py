"""Tes integrasi CLI run_experiment.py --quick."""

import csv
import os
import subprocess
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


class TestIntegration(unittest.TestCase):
    def test_quick_experiment_cli(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = os.path.join(
                temporary_directory, "hasil_quick"
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    os.path.join(PROJECT_ROOT, "run_experiment.py"),
                    "--quick",
                    "--out",
                    output_directory,
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(
                completed.returncode, 0, completed.stderr
            )

            evaluation_path = os.path.join(
                output_directory, "evaluasi.csv"
            )
            summary_path = os.path.join(
                output_directory, "ringkasan_run.csv"
            )
            self.assertTrue(os.path.exists(evaluation_path))
            self.assertTrue(os.path.exists(summary_path))

            with open(
                evaluation_path, newline="", encoding="utf-8"
            ) as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(
                    reader.fieldnames,
                    [
                        "metode",
                        "seed",
                        "evaluasi",
                        "makespan",
                        "best_so_far",
                        "valid",
                        "waktu_s",
                        "memori_kib",
                    ],
                )
                evaluation_rows = list(reader)

            self.assertEqual(len(evaluation_rows), 4 * 2 * 300)
            for row in evaluation_rows:
                if row["evaluasi"] == "300":
                    self.assertNotEqual(row["waktu_s"], "")
                    self.assertNotEqual(row["memori_kib"], "")
                else:
                    self.assertEqual(row["waktu_s"], "")
                    self.assertEqual(row["memori_kib"], "")

            with open(
                summary_path, newline="", encoding="utf-8"
            ) as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(
                    reader.fieldnames,
                    [
                        "metode",
                        "seed",
                        "best_makespan",
                        "eval_hingga_optimum",
                        "valid_best",
                        "waktu_s",
                        "memori_kib",
                    ],
                )
                summary_rows = list(reader)

            self.assertEqual(len(summary_rows), 4 * 2)


if __name__ == "__main__":
    unittest.main()
