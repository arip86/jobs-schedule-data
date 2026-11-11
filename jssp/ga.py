"""Genetic Algorithm untuk JSSP."""

import random
from typing import Sequence, Tuple

from . import RunResult
from .data import FT06
from .decoder import Evaluator
from .operators import crossover_segment, mutate_swap, random_chromosome


def run_ga(
    seed: int,
    budget: int = 3000,
    dataset: Sequence[Sequence[Tuple[int, int]]] = FT06,
    population_size: int = 40,
    elite: int = 1,
    crossover_probability: float = 0.85,
    mutation_probability: float = 0.15,
    validate_each: bool = False,
) -> RunResult:
    """Menjalankan GA sesuai parameter yang ditetapkan."""
    rng = random.Random(seed)
    evaluator = Evaluator(
        budget=budget, dataset=dataset, validate_each=validate_each
    )

    n_jobs = len(dataset)
    ops_per_job = len(dataset[0])

    population = []
    initial_size = min(population_size, budget)
    for _ in range(initial_size):
        chromosome = random_chromosome(rng, n_jobs, ops_per_job)
        makespan = evaluator.evaluate(chromosome)
        population.append((makespan, chromosome))

    generations = 0
    while evaluator.count < budget and population:
        population.sort(key=lambda item: item[0])

        if len(population) == 1:
            parent_pool = [population[0]]
        else:
            parent_pool = population[: max(1, len(population) // 2)]

        elite_item = population[0]
        target_children = min(
            population_size - elite, budget - evaluator.count
        )
        if target_children <= 0:
            break

        children = []
        for _ in range(target_children):
            parent1 = rng.choice(parent_pool)[1]
            parent2 = rng.choice(parent_pool)[1]

            if rng.random() < crossover_probability:
                child = crossover_segment(parent1, parent2, rng)
            else:
                child = list(parent1)

            if rng.random() < mutation_probability:
                child = mutate_swap(child, rng)

            makespan = evaluator.evaluate(child)
            children.append((makespan, child))

        generations += 1
        population = [elite_item] + children

    return RunResult(
        method="GA",
        seed=seed,
        evaluator=evaluator,
        generations=generations,
    )
