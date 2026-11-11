"""Dataset FT06 dan fungsi verifikasi data."""

from typing import Dict, Sequence, Tuple

# Setiap job adalah urutan (mesin, durasi). Indeks mesin dimulai dari 0.
FT06: Tuple[Tuple[Tuple[int, int], ...], ...] = (
    ((2, 1), (0, 3), (1, 6), (3, 7), (5, 3), (4, 6)),
    ((1, 8), (2, 5), (4, 10), (5, 10), (0, 10), (3, 4)),
    ((2, 5), (3, 4), (5, 8), (0, 9), (1, 1), (4, 7)),
    ((1, 5), (0, 5), (2, 5), (3, 3), (4, 8), (5, 9)),
    ((2, 9), (1, 3), (4, 5), (5, 4), (0, 3), (3, 1)),
    ((1, 3), (3, 3), (5, 9), (0, 10), (4, 4), (2, 1)),
)

N_JOBS = len(FT06)
N_MACHINES = 6
C_STAR = 55


def verify_dataset(
    dataset: Sequence[Sequence[Tuple[int, int]]] = FT06,
) -> Dict[str, object]:
    """Memeriksa struktur dataset dan mengembalikan statistiknya.

    Pemeriksaan mencakup: setiap job mengunjungi setiap mesin tepat sekali,
    total durasi per job, beban tiap mesin, total durasi, dan batas bawah
    sederhana. ValueError dilempar bila ada ketidakkonsistenan.
    """
    if len(dataset) == 0:
        raise ValueError("Dataset kosong")

    n_machines = max(machine for job in dataset for machine, _ in job) + 1
    expected_machines = set(range(n_machines))
    job_totals = []
    machine_loads = [0] * n_machines
    total_operations = 0

    for job_index, job in enumerate(dataset):
        if len(job) == 0:
            raise ValueError(f"Job {job_index} tidak memiliki operasi")

        machines = [machine for machine, _ in job]
        if len(machines) != len(set(machines)):
            raise ValueError(f"Job {job_index} mengunjungi mesin yang sama lebih dari sekali")
        if set(machines) != expected_machines:
            raise ValueError(
                f"Job {job_index} tidak mengunjungi semua mesin 0..{n_machines - 1}"
            )

        for machine, duration in job:
            if not isinstance(machine, int) or not isinstance(duration, int):
                raise ValueError("Mesin dan durasi harus berupa integer")
            if machine < 0 or machine >= n_machines:
                raise ValueError(f"Indeks mesin tidak valid pada job {job_index}")
            if duration < 0:
                raise ValueError(f"Durasi negatif pada job {job_index}")
            machine_loads[machine] += duration

        job_totals.append(sum(duration for _, duration in job))
        total_operations += len(job)

    total_duration = sum(job_totals)
    lower_bound = max(max(job_totals), max(machine_loads))

    return {
        "n_jobs": len(dataset),
        "n_machines": n_machines,
        "n_operations": total_operations,
        "job_totals": job_totals,
        "machine_loads": machine_loads,
        "total_duration": total_duration,
        "lower_bound": lower_bound,
    }
