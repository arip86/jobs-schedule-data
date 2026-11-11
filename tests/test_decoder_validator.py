"""Tes decoder dan validator."""

import random
import unittest

from jssp.data import C_STAR, FT06
from jssp.decoder import decode
from jssp.operators import random_chromosome
from jssp.validator import validate_schedule


class TestDecoderValidator(unittest.TestCase):
    def _sequential_chromosome(self):
        return [job for job in range(6) for _ in range(6)]

    def test_sequential_chromosome_is_valid(self):
        schedule, makespan = decode(self._sequential_chromosome())
        valid, errors = validate_schedule(schedule, FT06, makespan)
        self.assertTrue(valid, errors)
        self.assertGreaterEqual(makespan, C_STAR)

    def test_1000_random_chromosomes_are_valid_and_match(self):
        rng = random.Random(12345)
        for _ in range(1000):
            chromosome = random_chromosome(rng, 6, 6)
            schedule, makespan = decode(chromosome)
            valid, errors = validate_schedule(schedule, FT06, makespan)
            self.assertTrue(valid, errors)
            self.assertEqual(
                makespan, max(entry[4] for entry in schedule)
            )
            self.assertGreaterEqual(makespan, 47)

    def test_decoder_is_deterministic(self):
        chromosome = [3, 1, 4, 0, 5, 2] * 6
        schedule1, makespan1 = decode(chromosome)
        schedule2, makespan2 = decode(chromosome)
        self.assertEqual(schedule1, schedule2)
        self.assertEqual(makespan1, makespan2)

    def test_validator_detects_machine_overlap(self):
        schedule, _ = decode(self._sequential_chromosome())
        by_machine = {}
        for index, entry in enumerate(schedule):
            by_machine.setdefault(entry[2], []).append(index)

        machine, indices = next(
            (machine, indices)
            for machine, indices in by_machine.items()
            if len(indices) >= 2
        )
        first_index = indices[0]
        second_index = indices[1]
        first = schedule[first_index]
        second = schedule[second_index]

        new_start = first[3]
        new_end = new_start + (second[4] - second[3])
        corrupted = list(schedule)
        corrupted[second_index] = (
            second[0],
            second[1],
            second[2],
            new_start,
            new_end,
        )

        valid, errors = validate_schedule(corrupted, FT06, None)
        self.assertFalse(valid)
        self.assertTrue(
            any("Tumpang tindih" in error for error in errors), errors
        )

    def test_validator_detects_precedence_violation(self):
        schedule, _ = decode(self._sequential_chromosome())
        by_job = {}
        for index, entry in enumerate(schedule):
            by_job.setdefault(entry[0], []).append((entry[1], index))

        job = next(job for job, ops in by_job.items() if len(ops) >= 2)
        ops = sorted(by_job[job])
        first = schedule[ops[0][1]]
        second_index = ops[1][1]
        second = schedule[second_index]

        new_start = max(0, first[3] - 1)
        new_end = new_start + (second[4] - second[3])
        corrupted = list(schedule)
        corrupted[second_index] = (
            second[0],
            second[1],
            second[2],
            new_start,
            new_end,
        )

        valid, errors = validate_schedule(corrupted, FT06, None)
        self.assertFalse(valid)
        self.assertTrue(
            any("Precedence" in error for error in errors), errors
        )

    def test_validator_detects_wrong_duration(self):
        schedule, _ = decode(self._sequential_chromosome())
        entry = schedule[0]
        corrupted = list(schedule)
        corrupted[0] = (
            entry[0],
            entry[1],
            entry[2],
            entry[3],
            entry[4] + 1,
        )
        valid, errors = validate_schedule(corrupted, FT06, None)
        self.assertFalse(valid)
        self.assertTrue(
            any("Durasi" in error for error in errors), errors
        )

    def test_validator_detects_missing_operation(self):
        schedule, _ = decode(self._sequential_chromosome())
        corrupted = list(schedule)[1:]
        valid, errors = validate_schedule(corrupted, FT06, None)
        self.assertFalse(valid)
        self.assertTrue(
            any("hilang" in error for error in errors), errors
        )

    def test_validator_detects_duplicate_operation(self):
        schedule, _ = decode(self._sequential_chromosome())
        corrupted = list(schedule)
        corrupted.append(corrupted[0])
        valid, errors = validate_schedule(corrupted, FT06, None)
        self.assertFalse(valid)
        self.assertTrue(
            any("duplikat" in error for error in errors), errors
        )


if __name__ == "__main__":
    unittest.main()
