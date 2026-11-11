"""Smoke test aplikasi Streamlit."""

import unittest
from pathlib import Path

try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None


@unittest.skipIf(AppTest is None, "streamlit belum terpasang")
class StreamlitAppTest(unittest.TestCase):
    def test_app_runs_without_exception(self):
        app_path = Path(__file__).resolve().parents[1] / "streamlit_app.py"
        app = AppTest.from_file(
            str(app_path), default_timeout=60
        ).run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertIn(
            "Dashboard Hasil Eksperimen JSSP FT06",
            [title.value for title in app.title],
        )
        self.assertEqual(
            [tab.label for tab in app.tabs],
            [
                "Perbandingan",
                "Konvergensi",
                "Detail Run",
                "Big-O",
                "Validasi",
            ],
        )


if __name__ == "__main__":
    unittest.main()
