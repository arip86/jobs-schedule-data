"""Tes dataset FT06."""

import unittest

from jssp.data import C_STAR, FT06, verify_dataset


class TestData(unittest.TestCase):
    def test_ft06_statistics(self):
        info = verify_dataset(FT06)
        self.assertEqual(info["n_jobs"], 6)
        self.assertEqual(info["n_machines"], 6)
        self.assertEqual(info["n_operations"], 36)
        self.assertEqual(info["job_totals"], [26, 47, 34, 35, 25, 30])
        self.assertEqual(info["machine_loads"], [40, 26, 26, 22, 40, 43])
        self.assertEqual(info["total_duration"], 197)
        self.assertEqual(info["lower_bound"], 47)
        self.assertEqual(C_STAR, 55)

    def test_each_job_visits_each_machine_once(self):
        for job in FT06:
            self.assertEqual(len(job), 6)
            self.assertEqual(
                sorted(machine for machine, _ in job), list(range(6))
            )


if __name__ == "__main__":
    unittest.main()
