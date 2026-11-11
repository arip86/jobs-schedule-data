"""Operator genetik dan pergerakan tetangga."""

import random
from typing import List, Sequence, Tuple


def random_chromosome(
    rng: random.Random, n_jobs: int = 6, ops_per_job: int = 6
) -> List[int]:
    """Membuat kromosom acak dengan setiap job muncul `ops_per_job` kali."""
    chromosome = [job for job in range(n_jobs) for _ in range(ops_per_job)]
    rng.shuffle(chromosome)
    return chromosome


def crossover_segment(
    parent1: Sequence[int],
    parent2: Sequence[int],
    rng: random.Random,
) -> List[int]:
    """Crossover segmen yang menjaga multiset gen.

    Algoritma:
    1. Pilih segmen [a, b) secara acak.
    2. Salin parent1[a:b] ke anak pada posisi yang sama.
    3. Hitung sisa kuota setiap job setelah segmen disalin.
    4. Pindai parent2 dari kiri ke kanan dan isi posisi di luar segmen
       dengan gen yang kuotanya masih tersedia.
    5. Karena total kuota sama dengan panjang kromosom, semua posisi terisi
       dan jumlah kemunculan setiap job tetap sama.
    """
    if len(parent1) != len(parent2):
        raise ValueError("Panjang kedua induk harus sama")
    length = len(parent1)
    if length == 0:
        return []

    n_jobs = max(max(parent1), max(parent2)) + 1
    quota = [0] * n_jobs
    for gene in parent1:
        if gene < 0 or gene >= n_jobs:
            raise ValueError("Gen induk tidak valid")
        quota[gene] += 1

    counts_parent2 = [0] * n_jobs
    for gene in parent2:
        if gene < 0 or gene >= n_jobs:
            raise ValueError("Gen induk tidak valid")
        counts_parent2[gene] += 1
    if counts_parent2 != quota:
        raise ValueError("Kedua induk harus memiliki multiset gen yang sama")

    start_cut = rng.randrange(length)
    end_cut = rng.randrange(start_cut + 1, length + 1)

    child = [-1] * length
    remaining = quota[:]

    for position in range(start_cut, end_cut):
        gene = parent1[position]
        child[position] = gene
        remaining[gene] -= 1

    fill_positions = [
        position
        for position in range(length)
        if position < start_cut or position >= end_cut
    ]
    fill_index = 0
    for gene in parent2:
        if remaining[gene] > 0:
            if fill_index >= len(fill_positions):
                break
            child[fill_positions[fill_index]] = gene
            remaining[gene] -= 1
            fill_index += 1

    if any(gene < 0 for gene in child) or any(remaining):
        raise ValueError("Crossover gagal menjaga multiset gen")

    return child


def mutate_swap(chromosome: Sequence[int], rng: random.Random) -> List[int]:
    """Menukar dua posisi yang berisi nomor job berbeda."""
    result = list(chromosome)
    length = len(result)
    if length < 2:
        return result

    first = rng.randrange(length)
    candidates = [
        position
        for position in range(length)
        if result[position] != result[first]
    ]
    if not candidates:
        return result

    second = rng.choice(candidates)
    result[first], result[second] = result[second], result[first]
    return result


def neighbor_swap(chromosome: Sequence[int], first: int, second: int) -> List[int]:
    """Mengembalikan salinan kromosom dengan posisi first dan second ditukar."""
    result = list(chromosome)
    result[first], result[second] = result[second], result[first]
    return result


def random_swap_positions(
    chromosome: Sequence[int], rng: random.Random
) -> Tuple[int, int]:
    """Memilih dua posisi berbeda yang gennya berbeda."""
    length = len(chromosome)
    if length < 2:
        raise ValueError("Kromosom terlalu pendek untuk swap")

    first = rng.randrange(length)
    candidates = [
        position
        for position in range(length)
        if chromosome[position] != chromosome[first]
    ]
    if not candidates:
        candidates = [position for position in range(length) if position != first]

    second = rng.choice(candidates)
    return first, second
