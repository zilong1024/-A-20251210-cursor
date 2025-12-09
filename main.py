from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from app.data_loader import load_price_series, load_trades
from app.simulator import run_mark_to_market


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="交叉科技量化交易笔试题 - 逐日盯市计算器")
    parser.add_argument(
        "--trades",
        type=Path,
        default=Path("笔试题A/trades_cf.csv"),
        help="交易记录 CSV 路径（默认：笔试题A/trades_cf.csv）",
    )
    parser.add_argument(
        "--prices",
        type=Path,
        default=Path("笔试题A/cf2309.csv"),
        help="日线行情 CSV 路径（默认：笔试题A/cf2309.csv）",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="输出目录（默认：output）",
    )
    parser.add_argument(
        "--initial-balance",
        type=float,
        default=1_000_000.0,
        help="初始资金，默认 1,000,000",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    prices = load_price_series(args.prices)
    trades = load_trades(args.trades, prices["trade_date"])

    trade_df, position_df, balance_df = run_mark_to_market(
        trades=trades, prices=prices, initial_balance=args.initial_balance
    )

    # 输出 CSV
    trade_csv = args.output_dir / "trade.csv"
    position_csv = args.output_dir / "position.csv"
    balance_csv = args.output_dir / "balance.csv"

    trade_df.to_csv(trade_csv, index=False)
    position_df.to_csv(position_csv, index=False)
    balance_df.to_csv(balance_csv, index=False)

    # 输出 Excel 汇总
    excel_path = args.output_dir / "result.xlsx"
    with pd.ExcelWriter(excel_path) as writer:
        trade_df.to_excel(writer, sheet_name="trade", index=False)
        position_df.to_excel(writer, sheet_name="position", index=False)
        balance_df.to_excel(writer, sheet_name="balance", index=False)

    print(f"完成计算，文件已输出到 {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()

