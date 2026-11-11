"""Decoder berbasis representasi operasi dan penghitung evaluasi."""

from typing import List, Optional, Sequence, Tuple

from .data import C_STAR, FT06

ScheduleEntry = Tuple[int, int, int, int, int]
Interval = Tuple[int, int]


class BudgetExhausted(Exception):
    """Dilempar ketika evaluasi melebihi anggaran yang ditetapkan."""


def _dataset_dimensions(
    dataset: Sequence[Sequence[Tuple[int, int]]],
) -> Tuple[int, int]:
    n_jobs = len(dataset)
    if n_jobs == 0:
        raise ValueError("Dataset kosong")
    n_machines = max(machine for job in dataset for machine, _ in job) + 1
    return n_jobs, n_machines


def decode(
    chromosome: Sequence[int],
    dataset: Sequence[Sequence[Tuple[int, int]]] = FT06,
) -> Tuple[List[ScheduleEntry], int]:
    """Mendekode kromosom menjadi jadwal dan makespan.

    Kromosom berisi nomor job; kemunculan ke-k job j berarti operasi ke-k job j.
    Operasi ditempatkan pada celah kosong paling awal di mesin tujuannya yang
    dapat memuat durasi, dengan waktu mulai paling cepat sama dengan waktu
    selesai operasi sebelumnya pada job yang sama.
    """
    n_jobs, n_machines = _dataset_dimensions(dataset)
    expected_length = sum(len(job) for job in dataset)

    if len(chromosome) != expected_length:
        raise ValueError(
            f"Panjang kromosom {len(chromosome)} != {expected_length}"
        )

    counts = [0] * n_jobs
    for gene in chromosome:
        if not isinstance(gene, int) or isinstance(gene, bool):
            raise ValueError("Gen kromosom harus berupa integer")
        if gene < 0 or gene >= n_jobs:
            raise ValueError(f"Nomor job tidak valid: {gene}")
        counts[gene] += 1

    for job_index, job in enumerate(dataset):
        if counts[job_index] != len(job):
            raise ValueError(
                f"Job {job_index} muncul {counts[job_index]} kali, "
                f"seharusnya {len(job)}"
            )

    next_operation = [0] * n_jobs
    job_end = [0] * n_jobs
    machine_intervals: List[List[Interval]] = [[] for _ in range(n_machines)]
    schedule: List[ScheduleEntry] = []

    for gene in chromosome:
        operation_index = next_operation[gene]
        machine, duration = dataset[gene][operation_index]
        earliest = job_end[gene]

        start = earliest
        intervals = machine_intervals[machine]
        for interval_start, interval_end in intervals:
            if start + duration <= interval_start:
                break
            if start < interval_end:
                start = interval_end

        end = start + duration
        new_interval: Interval = (start, end)
        inserted = False
        for position, (interval_start, _) in enumerate(intervals):
            if start < interval_start:
                intervals.insert(position, new_interval)
                inserted = True
                break
        if not inserted:
            intervals.append(new_interval)

        job_end[gene] = end
        next_operation[gene] = operation_index + 1
        schedule.append((gene, operation_index, machine, start, end))

    makespan = max((entry[4] for entry in schedule), default=0)
    return schedule, makespan


class Evaluator:
    """Penghitung evaluasi terpusat untuk seluruh algoritma."""

    def __init__(
        self,
        budget: int = 3000,
        dataset: Sequence[Sequence[Tuple[int, int]]] = FT06,
        optimum: Optional[int] = C_STAR,
        validate_each: bool = False,
    ) -> None:
        self.budget = int(budget)
        self.dataset = dataset
        self.optimum = optimum
        self.validate_each = validate_each
        self.count = 0
        self.history: List[int] = []
        self.best_so_far: List[int] = []
        self.validity: List[bool] = []
        self.best_makespan: Optional[int] = None
        self.best_chrom: Optional[List[int]] = None
        self.best_schedule = None
        self.first_opt_eval: Optional[int] = None
        self.first_invalid = None

    @property
    def remaining(self) -> int:
        """Sisa evaluasi yang masih diizinkan."""
        return max(0, self.budget - self.count)

    def evaluate(self, chromosome: Sequence[int]) -> int:
        """Mendekode kromosom dan mencatat hasilnya sebagai satu evaluasi."""
        if self.count >= self.budget:
            raise BudgetExhausted(
                f"Anggaran evaluasi {self.budget} sudah habis"
            )

        schedule, makespan = decode(chromosome, self.dataset)
        self.count += 1
        self.history.append(makespan)

        if self.best_makespan is None or makespan < self.best_makespan:
            self.best_makespan = makespan
            self.best_chrom = list(chromosome)
            self.best_schedule = schedule

        self.best_so_far.append(self.best_makespan)

        if (
            self.optimum is not None
            and makespan == self.optimum
            and self.first_opt_eval is None
        ):
            self.first_opt_eval = self.count

        if self.validate_each:
            from .validator import validate_schedule

            valid, errors = validate_schedule(
                schedule, self.dataset, makespan
            )
            self.validity.append(valid)
            if not valid and self.first_invalid is None:
                self.first_invalid = (self.count, errors)

        return makespan
