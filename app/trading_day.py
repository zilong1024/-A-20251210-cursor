from __future__ import annotations

from datetime import date, datetime, time
from typing import Iterable, List


NIGHT_SESSION_START = time(hour=21, minute=0)


def map_datetime_to_trade_date(dt: datetime, trade_calendar: Iterable[date]) -> date:
    """
    将自然时间映射为交易日：
    - 21:00 之后的夜盘归入下一个交易日（遇周末/节假日按下一个存在于 trade_calendar 的日期递推）。
    - 其余时间归入当日，如果当日不在日历中，则顺延到下一个存在的交易日。
    """
    trade_days: List[date] = sorted(trade_calendar)
    candidate = dt.date()
    if dt.time() >= NIGHT_SESSION_START:
        candidate = candidate.fromordinal(candidate.toordinal() + 1)

    for trade_day in trade_days:
        if trade_day >= candidate:
            return trade_day

    raise ValueError(f"无法为时间 {dt.isoformat()} 映射交易日，请检查行情日历。")


