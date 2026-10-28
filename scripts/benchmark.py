
import argparse
import json
import time
import tracemalloc
from pathlib import Path

from datarecon.reconciliation import reconcile


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark DataRecon reconciliation performance."
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

    tracemalloc.start()
    start = time.perf_counter()

    report = reconcile(
        str(source_path),
        str(target_path),
        args.output,
    )

    elapsed = time.perf_counter() - start
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    row_count = report["source"]["row_count"]
    result = {
        "source_file": str(source_path),
        "target_file": str(target_path),
        "source_rows": row_count,
        "target_rows": report["target"]["row_count"],
        "elapsed_seconds": round(elapsed, 4),
        "source_rows_per_second": round(
            row_count / elapsed if elapsed else 0, 2
        ),
        "peak_traced_python_memory_mb": round(
            peak_memory / (1024 * 1024), 2
        ),
        "reconciliation_matched": report["reconciliation"]["matched"],
        "source_only_count": report["reconciliation"]["source_only_count"],
        "target_only_count": report["reconciliation"]["target_only_count"],
        "field_mismatch_count": report["reconciliation"]["field_mismatch_count"],
    }

    results_path = Path(args.results)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2))
    print(f"\nBenchmark results saved to: {results_path}")


if __name__ == "__main__":
    main()
