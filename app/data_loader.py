from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd

from .trading_day import map_datetime_to_trade_date


@dataclass
class TradeRecord:
    symbol: str
    open_dt: datetime
    cover_dt: datetime
    open_trade_date: date
    cover_trade_date: date
    direction: int  # 1 for long, -1 for short
    volume: int
    open_price: float
    cover_price: float
    fee_total_ticks: float
    tick_size: float
    size: float
    open_commission: float
    close_commission: float


def load_price_series(price_path: Path) -> pd.DataFrame:
    """
    读取日线行情数据，返回包含 trade_date(date) 和 close(float) 的 DataFrame（按日期升序）。
    """
    df = pd.read_csv(price_path, encoding="gbk", header=1)
    df = df.rename(columns={"trade_date": "trade_date", "close": "close"})
    df = df[["trade_date", "close"]].copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d").dt.date
    df["close"] = df["close"].astype(float)
    df = df.sort_values("trade_date").reset_index(drop=True)
    return df


def _parse_datetime(text: str) -> datetime:
    return datetime.strptime(text, "%Y/%m/%d %H:%M")


def load_trades(trades_path: Path, trade_calendar: Iterable[date]) -> List[TradeRecord]:
    """
    读取交易记录，跳过表头行，补充开仓交易日映射，计算手续费（货币单位）。
    """
    df = pd.read_csv(trades_path, encoding="gbk", header=1)

    # 兼容中英文列名
    if "表头注释" not in df.columns and "index" in df.columns:
        df = df.rename(
            columns={
                "index": "表头注释",
                "open_time": "开仓时间",
                "cover_time": "平仓时间",
                "open_price": "开仓价格",
                "cover_price": "平仓价格",
                "ls": "多空方向",
                "cover_date": "平仓交易日",
                "symbol": "合约代码",
                "volume": "成交量",
                "rt": "收益",
                "fee": "手续费",
                "tick_size": "最小报价单位",
                "size": "交易单位",
            }
        )

    df = df[df["表头注释"] != "index"].copy()
    records: List[TradeRecord] = []
    trade_days = set(trade_calendar)

    for _, row in df.iterrows():
        open_dt = _parse_datetime(str(row["开仓时间"]))
        cover_dt = _parse_datetime(str(row["平仓时间"]))
        open_trade_date = map_datetime_to_trade_date(open_dt, trade_days)
        cover_trade_date = datetime.strptime(
            str(int(row["平仓交易日"])), "%Y%m%d"
        ).date()

        direction = int(row["多空方向"])
        volume = int(row["成交量"])
        size = float(row["交易单位"])
        tick_size = float(row["最小报价单位"])
        fee_total_ticks = float(row["手续费"])
        fee_half = fee_total_ticks / 2
        commission = fee_half * tick_size * size * volume

        records.append(
            TradeRecord(
                symbol=str(row["合约代码"]),
                open_dt=open_dt,
                cover_dt=cover_dt,
                open_trade_date=open_trade_date,
                cover_trade_date=cover_trade_date,
                direction=direction,
                volume=volume,
                open_price=float(row["开仓价格"]),
                cover_price=float(row["平仓价格"]),
                fee_total_ticks=fee_total_ticks,
                tick_size=tick_size,
                size=size,
                open_commission=commission,
                close_commission=commission,
            )
        )

    return records


def derive_trade_date_window(trades: List[TradeRecord]) -> Tuple[date, date]:
    """获得交易日窗口，用于裁剪行情日历。"""
    min_day = min(r.open_trade_date for r in trades)
    max_day = max(r.cover_trade_date for r in trades)
    return min_day, max_day

