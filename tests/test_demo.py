from pathlib import Path

import pandas as pd
import pandas.testing as pdt

from app.data_loader import load_price_series, load_trades
from app.simulator import run_mark_to_market


BASE = Path("/home/h3c/笔试题A/笔试题A")


def test_demo_matches_expected():
    prices = load_price_series(BASE / "cf2309.csv")
    trades = load_trades(BASE / "demo/trades_cf_demo.csv", prices["trade_date"])

    trade_df, position_df, balance_df = run_mark_to_market(trades, prices)

    xls = pd.ExcelFile(BASE / "demo/三表输出结果示例.xlsx")
    exp_trade = pd.read_excel(xls, sheet_name="trade")
    exp_position = pd.read_excel(xls, sheet_name="position")
    exp_balance = pd.read_excel(xls, sheet_name="balance")

    # 对齐列顺序
    trade_df = trade_df[exp_trade.columns]
    position_df = position_df[exp_position.columns]
    balance_df = balance_df[exp_balance.columns]

    # 统一日期类型
    for df in (trade_df, exp_trade):
        if "Open_trade_datetime" in df.columns:
            df["Open_trade_datetime"] = pd.to_datetime(df["Open_trade_datetime"])
        if "Close_trade_datetime" in df.columns:
            df["Close_trade_datetime"] = pd.to_datetime(df["Close_trade_datetime"])
    for df in (position_df, exp_position, balance_df, exp_balance):
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date

    pdt.assert_frame_equal(
        trade_df.reset_index(drop=True),
        exp_trade.reset_index(drop=True),
        check_dtype=False,
        check_exact=False,
        rtol=1e-6,
        atol=1e-6,
    )
    pdt.assert_frame_equal(
        position_df.reset_index(drop=True),
        exp_position.reset_index(drop=True),
        check_dtype=False,
        check_exact=False,
        rtol=1e-6,
        atol=1e-6,
    )
    pdt.assert_frame_equal(
        balance_df.reset_index(drop=True),
        exp_balance.reset_index(drop=True),
        check_dtype=False,
        check_exact=False,
        rtol=1e-6,
        atol=1e-6,
    )

