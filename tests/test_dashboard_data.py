"""Tes pemuatan data dashboard Streamlit."""

import tempfile
import unittest
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    pd = None


@unittest.skipIf(pd is None, "pandas belum terpasang")
class DashboardDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from dashboard_data import (
            average_convergence,
            downsample_convergence,
            filter_methods,
            load_dashboard_data,
        )

        cls.average_convergence = staticmethod(average_convergence)
        cls.downsample_convergence = staticmethod(
            downsample_convergence
        )
        cls.filter_methods = staticmethod(filter_methods)
        cls.load_dashboard_data = staticmethod(load_dashboard_data)
        cls.hasil = Path(__file__).resolve().parents[1] / "hasil"

    def test_load_all_files(self):
        data = self.load_dashboard_data(str(self.hasil))
        self.assertEqual(
            set(data),
            {
                "evaluasi",
                "ringkasan_run",
                "tabel_ringkasan",
                "big_o",
                "validasi_sampel",
            },
        )
        self.assertEqual(len(data["evaluasi"]), 60000)
        self.assertEqual(len(data["ringkasan_run"]), 20)
        self.assertEqual(len(data["tabel_ringkasan"]), 4)
        self.assertEqual(len(data["big_o"]), 5)
        self.assertEqual(len(data["validasi_sampel"]), 4)
        self.assertTrue(data["evaluasi"]["valid"].all())
        self.assertTrue(data["ringkasan_run"]["valid_best"].all())

    def test_average_convergence_has_full_series(self):
        data = self.load_dashboard_data(str(self.hasil))
        convergence = self.average_convergence(data["evaluasi"])
        self.assertEqual(len(convergence), 4 * 3000)
        self.assertEqual(
            set(convergence.columns),
            {"metode", "evaluasi", "rata_rata_best_so_far"},
        )
        self.assertEqual(convergence["evaluasi"].max(), 3000)

    def test_filter_methods(self):
        data = self.load_dashboard_data(str(self.hasil))
        filtered = self.filter_methods(
            data["ringkasan_run"], ["GA"]
        )
        self.assertEqual(set(filtered["metode"]), {"GA"})
        self.assertEqual(len(filtered), 5)

    def test_downsample_convergence(self):
        data = self.load_dashboard_data(str(self.hasil))
        sampled = self.downsample_convergence(
            data["evaluasi"], step=10
        )
        self.assertIn(3000, set(sampled["evaluasi"]))
        self.assertTrue((sampled["evaluasi"] % 10 == 0).all())

    def test_missing_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(FileNotFoundError):
                self.load_dashboard_data(temporary)


if __name__ == "__main__":
    unittest.main()
