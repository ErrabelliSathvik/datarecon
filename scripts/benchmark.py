import argparse
import json
import time
import tracemalloc
from pathlib import Path

from datarecon.reconciliation import reconcile


def main():
    parser = argparse.ArgumentParser(
        description="Measure DataRecon reconciliation performance."
    )
    parser.add_argument(
        "--source",
        default="data/generated/source_orders.csv",
    )
    parser.add_argument(
        "--target",
        default="data/generated/target_orders.csv",
    )
    parser.add_argument(
        "--output",
        default="outputs/benchmark",
    )
    parser.add_argument(
        "--results",
        default="outputs/benchmark/performance.json",
    )
    args = parser.parse_args()

    source_path = Path(args.source)
    target_path = Path(args.target)

    if not source_path.exists() or not target_path.exists():
        raise FileNotFoundError(
            "Input files not found. Run scripts/generate_data.py first."
        )

    # Measure execution time and traced Python memory.
    tracemalloc.start()
    start_time = time.perf_counter()

    report = reconcile(
        str(source_path),
        str(target_path),
        args.output,
    )

    elapsed = time.perf_counter() - start_time
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    source_rows = report["source"]["row_count"]
    target_rows = report["target"]["row_count"]
    reconciliation = report["reconciliation"]

    results = {
        "source_file": str(source_path),
        "target_file": str(target_path),
        "source_rows": source_rows,
        "target_rows": target_rows,
        "elapsed_seconds": round(elapsed, 4),
        "source_rows_per_second": round(
            source_rows / elapsed if elapsed else 0, 2
        ),
        "peak_traced_python_memory_mb": round(
            peak_memory / (1024 * 1024), 2
        ),
        "reconciliation_matched": reconciliation["matched"],
        "source_only_count": reconciliation["source_only_count"],
        "target_only_count": reconciliation["target_only_count"],
        "field_mismatch_count": reconciliation["field_mismatch_count"],
    }

    results_path = Path(args.results)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(results, indent=2))
    print(f"\nBenchmark results saved to: {results_path}")


if __name__ == "__main__":
    main()
