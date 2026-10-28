
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def generate_orders(count: int, seed: int) -> pd.DataFrame:
    """Generate deterministic synthetic order data."""

    if count < 0:
        raise ValueError("count must not be negative")

    rng = np.random.default_rng(seed)

    order_ids = np.arange(100001, 100001 + count)

    dates = pd.Timestamp("2026-01-01") + pd.to_timedelta(
        rng.integers(0, 300, size=count),
        unit="D",
    )

    return pd.DataFrame({
        "order_id": order_ids.astype(str),
        "customer_id": [
            f"C{value:05d}"
            for value in rng.integers(1, max(2, count // 3 + 2), size=count)
        ],
        "order_date": dates.strftime("%Y-%m-%d"),
        "amount": np.round(rng.uniform(10, 10000, size=count), 2),
        "status": rng.choice(
            ["pending", "completed", "shipped", "cancelled"],
            size=count,
        ),
    })


def main():
    parser = argparse.ArgumentParser(
        description="Generate reproducible synthetic order data."
    )
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="data/generated")
    args = parser.parse_args()

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    source = generate_orders(args.rows, args.seed)
    target = source.copy()

    # Deliberately introduce reconciliation differences.
    if len(target) >= 3:
        target.loc[0, "amount"] = round(
            float(target.loc[0, "amount"]) + 25.00, 2
        )
        target = target.drop(index=1).reset_index(drop=True)

        extra = generate_orders(1, args.seed + 1)
        extra["order_id"] = str(900000000 + args.seed)
        target = pd.concat([target, extra], ignore_index=True)

    source.to_csv(output / "source_orders.csv", index=False)
    target.to_csv(output / "target_orders.csv", index=False)

    print(f"Generated {len(source)} source records")
    print(f"Generated {len(target)} target records")
    print(f"Output directory: {output.resolve()}")


if __name__ == "__main__":
    main()
