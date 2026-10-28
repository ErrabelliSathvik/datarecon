import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def generate_orders(count: int, seed: int) -> pd.DataFrame:
    """Create repeatable sample order records."""

    if count < 0:
        raise ValueError("count must not be negative")

    rng = np.random.default_rng(seed)
    order_ids = np.arange(100001, 100001 + count)

    dates = pd.Timestamp("2026-01-01") + pd.to_timedelta(
        rng.integers(0, 300, size=count),
        unit="D",
    )

    orders = pd.DataFrame({
        "order_id": order_ids.astype(str),
        "customer_id": [
            f"C{value:05d}"
            for value in rng.integers(
                1, max(2, count // 3 + 2), size=count
            )
        ],
        "order_date": dates.strftime("%Y-%m-%d"),
        "amount": np.round(rng.uniform(10, 10000, size=count), 2),
        "status": rng.choice(
            ["pending", "completed", "shipped", "cancelled"],
            size=count,
        ),
    })

    return orders


def main():
    parser = argparse.ArgumentParser(
        description="Generate repeatable sample order datasets."
    )
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="data/generated")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    source = generate_orders(args.rows, args.seed)
    target = source.copy()

    # Add a few differences so reconciliation has something to detect.
    if len(target) >= 3:
        target.loc[0, "amount"] = round(
            float(target.loc[0, "amount"]) + 25.00, 2
        )

        target = target.drop(index=1).reset_index(drop=True)

        extra_order = generate_orders(1, args.seed + 1)
        extra_order["order_id"] = str(900000000 + args.seed)

        target = pd.concat(
            [target, extra_order],
            ignore_index=True,
        )

    source.to_csv(output_dir / "source_orders.csv", index=False)
    target.to_csv(output_dir / "target_orders.csv", index=False)

    print(f"Generated {len(source)} source records")
    print(f"Generated {len(target)} target records")
    print(f"Output directory: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
