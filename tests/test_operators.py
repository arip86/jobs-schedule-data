"""Tes operator genetik."""

import random
import unittest

from jssp.operators import (
    crossover_segment,
    mutate_swap,
    neighbor_swap,
    random_chromosome,
)


class TestOperators(unittest.TestCase):
    def test_crossover_preserves_multiset(self):
        rng = random.Random(1)
        parent1 = random_chromosome(rng, 6, 6)
        parent2 = random_chromosome(rng, 6, 6)

        for _ in range(500):
            child = crossover_segment(parent1, parent2, rng)
            self.assertEqual(len(child), 36)
            self.assertEqual(
                [child.count(job) for job in range(6)], [6] * 6
            )
            self.assertEqual(sorted(child), sorted(parent1))

    def test_mutation_changes_chromosome_and_preserves_multiset(self):
        rng = random.Random(2)
        parent = random_chromosome(rng, 6, 6)

        for _ in range(500):
            child = mutate_swap(parent, rng)
            self.assertEqual(len(child), 36)
            self.assertNotEqual(child, parent)
            self.assertEqual(sorted(child), sorted(parent))
            self.assertEqual(
                [child.count(job) for job in range(6)], [6] * 6
            )
            self.assertEqual(
                sum(1 for a, b in zip(child, parent) if a != b), 2
            )

    def test_neighbor_swap_only_swaps_two_positions(self):
        rng = random.Random(3)
        parent = random_chromosome(rng, 6, 6)
        first, second = 0, 1
        while parent[first] == parent[second]:
            first = rng.randrange(36)
            second = rng.randrange(36)

        child = neighbor_swap(parent, first, second)
        self.assertEqual(len(child), 36)
        for index in range(36):
            if index not in (first, second):
                self.assertEqual(child[index], parent[index])
        self.assertEqual(child[first], parent[second])
        self.assertEqual(child[second], parent[first])
        self.assertEqual(
            sum(1 for a, b in zip(child, parent) if a != b), 2
        )


if __name__ == "__main__":
    unittest.main()
