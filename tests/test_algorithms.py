"""Tes algoritma dan konsistensi anggaran evaluasi."""

import unittest

from jssp.data import FT06
from jssp.ga import run_ga
from jssp.random_search import run_random_search
from jssp.sa import run_sa
from jssp.ts import run_ts, select_candidate
from jssp.validator import validate_schedule


class TestAlgorithms(unittest.TestCase):
    def _assert_common(self, result, budget, expect_validity=False):
        evaluator = result.evaluator
        self.assertEqual(evaluator.count, budget)
        self.assertEqual(len(evaluator.history), budget)
        self.assertEqual(len(evaluator.best_so_far), budget)

        for previous, current in zip(
            evaluator.best_so_far, evaluator.best_so_far[1:]
        ):
            self.assertLessEqual(current, previous)

        self.assertIsNotNone(evaluator.best_makespan)
        self.assertIsNotNone(evaluator.best_schedule)
        valid, errors = validate_schedule(
            evaluator.best_schedule, FT06, evaluator.best_makespan
        )
        self.assertTrue(valid, errors)

        if expect_validity:
            self.assertEqual(len(evaluator.validity), budget)
            self.assertTrue(all(evaluator.validity))

    def test_small_budget_300(self):
        runners = [run_ga, run_sa, run_ts, run_random_search]
        for index, runner in enumerate(runners):
            with self.subTest(runner=runner.__name__):
                result = runner(
                    seed=100 + index, budget=300, validate_each=True
                )
                self._assert_common(result, 300, expect_validity=True)

    def test_reproducibility(self):
        runners = [run_ga, run_sa, run_ts, run_random_search]
        for runner in runners:
            with self.subTest(runner=runner.__name__):
                first = runner(seed=42, budget=300)
                second = runner(seed=42, budget=300)
                different = runner(seed=43, budget=300)
                self.assertEqual(
                    first.evaluator.history, second.evaluator.history
                )
                self.assertNotEqual(
                    first.evaluator.history, different.evaluator.history
                )

    def test_full_budget_3000(self):
        cases = [
            (run_ga, 2026),
            (run_sa, 2126),
            (run_ts, 2226),
            (run_random_search, 2326),
        ]
        for runner, seed in cases:
            with self.subTest(runner=runner.__name__):
                result = runner(seed=seed, budget=3000)
                self._assert_common(result, 3000)

    def test_ga_generation_count(self):
        result = run_ga(seed=2026, budget=3000)
        self.assertGreaterEqual(result.generations, 75)
        self.assertLessEqual(result.generations, 77)

    def test_ts_iteration_count(self):
        result = run_ts(seed=2226, budget=3000)
        self.assertGreaterEqual(result.iterations, 99)
        self.assertLessEqual(result.iterations, 101)

    def test_sa_temperatures(self):
        result = run_sa(seed=2126, budget=3000)
        self.assertIn(1500, result.temperatures)
        self.assertIn(3000, result.temperatures)
        self.assertGreaterEqual(result.temperatures[1500], 1.0)
        self.assertLessEqual(result.temperatures[1500], 1.2)
        self.assertGreaterEqual(result.temperatures[3000], 0.010)
        self.assertLessEqual(result.temperatures[3000], 0.014)

    def test_ts_tabu_selection_and_aspiration(self):
        tabu_candidate = (10, (0, 1), [0])
        other_candidate = (12, (0, 2), [1])

        selected = select_candidate(
            [tabu_candidate, other_candidate],
            {(0, 1): 10},
            iteration=5,
            best_makespan=10,
        )
        self.assertEqual(selected[1], (0, 2))

        aspirated_candidate = (9, (0, 1), [0])
        selected = select_candidate(
            [aspirated_candidate, other_candidate],
            {(0, 1): 10},
            iteration=5,
            best_makespan=10,
        )
        self.assertEqual(selected[1], (0, 1))

        selected = select_candidate(
            [tabu_candidate, other_candidate],
            {(0, 1): 10, (0, 2): 10},
            iteration=5,
            best_makespan=5,
        )
        self.assertEqual(selected[1], (0, 1))


if __name__ == "__main__":
    unittest.main()
