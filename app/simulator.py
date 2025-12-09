from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Iterable, List, Tuple

import pandas as pd

from .data_loader import TradeRecord, derive_trade_date_window


@dataclass
class PositionLot:
    symbol: str
    direction: int  # 1 long, -1 short
    volume: int
    open_price: float
    open_trade_date: date
    size: float


def build_trade_table(trades: List[TradeRecord]) -> pd.DataFrame:
    """生成 trade 表 DataFrame。"""
    rows = []
    for idx, t in enumerate(trades):
        open_num = t.volume if t.direction > 0 else -t.volume
        close_num = -t.volume if t.direction > 0 else t.volume
        rows.append(
            {
                "Unnamed: 0": idx,
                "Ticker": t.symbol,
                "Open_trade_datetime": t.open_dt,
                "Open_trade_price": t.open_price,
                "Open_trade_num": open_num,
                "size": t.size,
                "open_commission": t.open_commission,
                "Close_trade_datetime": t.cover_dt,
                "Close_trade_price": t.cover_price,
                "Close_trade_num": close_num,
                "close_commission": t.close_commission,
            }
        )
    return pd.DataFrame(rows)


def run_mark_to_market(
    trades: List[TradeRecord],
    prices: pd.DataFrame,
    initial_balance: float = 1_000_000.0,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    按交易日逐日盯市，返回 (trade_df, position_df, balance_df)。
    prices: 必须包含列 trade_date(date), close(float)。
    """
    if not trades:
        raise ValueError("交易记录为空。")

    start_date, end_date = derive_trade_date_window(trades)
    prices = prices[(prices["trade_date"] >= start_date) & (prices["trade_date"] <= end_date)]
    prices = prices.sort_values("trade_date").reset_index(drop=True)
    price_map: Dict[date, float] = dict(zip(prices["trade_date"], prices["close"]))

    open_by_date: Dict[date, List[TradeRecord]] = {}
    close_by_date: Dict[date, List[TradeRecord]] = {}
    for t in trades:
        open_by_date.setdefault(t.open_trade_date, []).append(t)
        close_by_date.setdefault(t.cover_trade_date, []).append(t)

    positions: List[PositionLot] = []
    balance_rows: List[Dict] = []
    position_rows: List[Dict] = []

    prev_balance = initial_balance
    cum_pnl = 0.0
    prev_net = 1.0
    prev_close = None

    trade_df = build_trade_table(trades)

    for _, price_row in prices.iterrows():
        trade_day: date = price_row["trade_date"]
        close_price: float = float(price_row["close"])

        trade_pnl = 0.0
        trade_cost = 0.0

        # 汇总当日事件，保证开仓在平仓前处理。
        events: List[Tuple[datetime, str, TradeRecord]] = []
        for t in open_by_date.get(trade_day, []):
            events.append((t.open_dt, "open", t))
        for t in close_by_date.get(trade_day, []):
            events.append((t.cover_dt, "close", t))
        events.sort(key=lambda e: (e[0], 0 if e[1] == "open" else 1))

        # 处理事件
        for _, event_type, t in events:
            if event_type == "open":
                trade_cost += t.open_commission
                positions.append(
                    PositionLot(
                        symbol=t.symbol,
                        direction=t.direction,
                        volume=t.volume,
                        open_price=t.open_price,
                        open_trade_date=t.open_trade_date,
                        size=t.size,
                    )
                )
            else:  # close
                trade_cost += t.close_commission
                remaining = t.volume
                # 按 FIFO 关闭同方向持仓
                idx = 0
                while remaining > 0 and idx < len(positions):
                    lot = positions[idx]
                    if lot.direction != t.direction:
                        idx += 1
                        continue
                    qty = min(remaining, lot.volume)
                    base_price = (
                        lot.open_price if lot.open_trade_date == trade_day else prev_close
                    )
                    if base_price is None:
                        raise ValueError("缺少前一交易日收盘价，无法计算平仓盈亏。")
                    trade_pnl += (t.cover_price - base_price) * t.direction * lot.size * qty
                    lot.volume -= qty
                    remaining -= qty
                    if lot.volume == 0:
                        positions.pop(idx)
                    else:
                        idx += 1
                if remaining > 0:
                    raise ValueError(f"{trade_day} 平仓数量超出持仓，请检查数据。")

        # 计算当日持仓盈亏
        hold_pnl = 0.0
        for lot in positions:
            base_price = (
                lot.open_price if lot.open_trade_date == trade_day else prev_close
            )
            if base_price is None:
                raise ValueError("缺少前一交易日收盘价，无法计算持仓盈亏。")
            hold_pnl += (close_price - base_price) * lot.direction * lot.size * lot.volume

        total_pnl = trade_pnl + hold_pnl - trade_cost
        cum_pnl += total_pnl
        balance = prev_balance + total_pnl
        daily_return = total_pnl / prev_balance if prev_balance != 0 else 0.0
        net = prev_net * (1 + daily_return)

        net_position = sum(l.direction * l.volume for l in positions)
        market_value = abs(net_position) * close_price * (positions[0].size if positions else 0.0)

        balance_rows.append(
            {
                "Unnamed: 0": len(balance_rows),
                "date": trade_day,
                "hold_pnl": hold_pnl,
                "trade_pnl": trade_pnl,
                "trade_cost": trade_cost,
                "total_pnl": total_pnl,
                "market_value": market_value,
                "cum_pnl": cum_pnl,
                "balance": balance,
                "return": daily_return,
                "net": net,
            }
        )

        # 生成当日收盘持仓表（区分多空）
        if positions:
            for direction in (1, -1):
                lots = [l for l in positions if l.direction == direction]
                if not lots:
                    continue
                total_vol = sum(l.volume for l in lots)
                weighted_cost_sum = 0.0
                for l in lots:
                    base_price = l.open_price if l.open_trade_date == trade_day else prev_close
                    weighted_cost_sum += base_price * l.volume
                cost_price = weighted_cost_sum / total_vol
                position_rows.append(
                    {
                        "date": trade_day,
                        "ticker": lots[0].symbol,
                        "drt": direction,
                        "cost_price": cost_price,
                        "close_price": close_price,
                        "number": direction * total_vol,
                    }
                )

        prev_balance = balance
        prev_net = net
        prev_close = close_price

    trade_df = trade_df.sort_values("Unnamed: 0").reset_index(drop=True)
    position_df = pd.DataFrame(position_rows)
    balance_df = pd.DataFrame(balance_rows)

    return trade_df, position_df, balance_df

