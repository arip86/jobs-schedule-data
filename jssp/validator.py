"""Validator jadwal hasil decoder."""

from typing import Dict, List, Optional, Sequence, Tuple

from .data import FT06

ScheduleEntry = Tuple[int, int, int, int, int]


def validate_schedule(
    schedule: Sequence[ScheduleEntry],
    dataset: Sequence[Sequence[Tuple[int, int]]] = FT06,
    expected_makespan: Optional[int] = None,
) -> Tuple[bool, List[str]]:
    """Memeriksa jadwal dan mengembalikan (valid, daftar_error).

    Pemeriksaan: jumlah operasi, keunikan (job, op_idx), kesesuaian mesin dan
    durasi, durasi/start, precedence job, tumpang tindih mesin, dan makespan.
    """
    errors: List[str] = []

    if not isinstance(schedule, (list, tuple)):
        return False, ["Jadwal bukan list atau tuple"]

    entries = list(schedule)
    n_jobs = len(dataset)
    expected_operations = sum(len(job) for job in dataset)

    if len(entries) != expected_operations:
        errors.append(
            f"Jumlah operasi {len(entries)} != {expected_operations}"
        )

    seen: Dict[Tuple[int, int], ScheduleEntry] = {}
    parsed: List[Tuple[int, int, int, int, int, int]] = []

    for index, entry in enumerate(entries):
        if not isinstance(entry, (list, tuple)) or len(entry) != 5:
            errors.append(f"Entri {index} bukan jadwal operasi yang valid")
            continue

        job, operation_index, machine, start, end = entry
        values = (job, operation_index, machine, start, end)
        if not all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in values
        ):
            errors.append(f"Entri {index} berisi nilai non-integer")
            continue

        if job < 0 or job >= n_jobs:
            errors.append(f"Job tidak valid pada entri {index}: {job}")
            continue
        if operation_index < 0 or operation_index >= len(dataset[job]):
            errors.append(
                f"Indeks operasi tidak valid pada entri {index}: "
                f"({job}, {operation_index})"
            )
            continue

        key = (job, operation_index)
        if key in seen:
            errors.append(f"Operasi {key} duplikat")
        else:
            seen[key] = entry

        expected_machine, expected_duration = dataset[job][operation_index]
        if machine != expected_machine:
            errors.append(
                f"Mesin operasi {key} adalah {machine}, "
                f"seharusnya {expected_machine}"
            )
        if end - start != expected_duration:
            errors.append(
                f"Durasi operasi {key} adalah {end - start}, "
                f"seharusnya {expected_duration}"
            )
        if start < 0:
            errors.append(f"Start operasi {key} negatif: {start}")
        if end < start:
            errors.append(f"End operasi {key} lebih kecil dari start")

        parsed.append(
            (job, operation_index, machine, start, end, expected_duration)
        )

    for job_index, job in enumerate(dataset):
        for operation_index in range(len(job)):
            if (job_index, operation_index) not in seen:
                errors.append(
                    f"Operasi ({job_index}, {operation_index}) hilang"
                )

    for job_index, job in enumerate(dataset):
        for operation_index in range(1, len(job)):
            previous = seen.get((job_index, operation_index - 1))
            current = seen.get((job_index, operation_index))
            if previous is not None and current is not None:
                if current[3] < previous[4]:
                    errors.append(
                        "Precedence dilanggar pada job "
                        f"{job_index}: operasi {operation_index} mulai "
                        f"sebelum operasi {operation_index - 1} selesai"
                    )

    by_machine: Dict[int, List[Tuple[int, int, int, int]]] = {}
    for job, operation_index, machine, start, end, _ in parsed:
        by_machine.setdefault(machine, []).append(
            (start, end, job, operation_index)
        )

    for machine, intervals in by_machine.items():
        intervals.sort(key=lambda item: (item[0], item[1]))
        for position in range(1, len(intervals)):
            previous = intervals[position - 1]
            current = intervals[position]
            if current[0] < previous[1]:
                errors.append(
                    "Tumpang tindih mesin "
                    f"{machine}: operasi ({current[2]}, {current[3]}) "
                    f"mulai {current[0]} sebelum operasi "
                    f"({previous[2]}, {previous[3]}) selesai {previous[1]}"
                )

    if parsed:
        recomputed = max(entry[4] for entry in parsed)
        if expected_makespan is not None and recomputed != expected_makespan:
            errors.append(
                f"Makespan hasil hitung ulang {recomputed} != "
                f"{expected_makespan}"
            )

    return len(errors) == 0, errors
