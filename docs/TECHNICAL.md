# 技术文档：交叉科技量化交易笔试题

## 1. 概览
- 目标：基于 `trades_cf.csv` 与 `cf2309.csv`，按逐日盯市生成三张表：`trade`、`position`、`balance`。
- 语言/依赖：Python 3.10，`pandas`、`openpyxl`、`PyPDF2`（读取题面用）。
- 初始资金：1,000,000。
- 输出位置：`output/trade.csv`、`output/position.csv`、`output/balance.csv`，以及汇总 Excel `output/result.xlsx`。

## 2. 数据与字段
- 交易表 `trades_cf.csv`（GBK 编码，首行中文表头、第二行英文表头）关键字段：
  - 开仓/平仓时间：`开仓时间`、`平仓时间`
  - 开平价：`开仓价格`、`平仓价格`
  - 多空方向：`多空方向`（1=多，-1=空）
  - 平仓交易日：`平仓交易日`（交易日维度，夜盘归次日）
  - 成交量：`成交量`；最小报价单位：`最小报价单位`；交易单位（合约乘数）：`交易单位`
  - 手续费：`手续费`（开+平合计，单位为 tick 数）
- 日线行情 `cf2309.csv`（GBK，header=1）：使用 `trade_date` 与 `close`。

## 3. 交易日映射
- 规则：21:00 之后的夜盘归入下一个交易日；若遇周末/节假日，顺延到行情日历中的下一有效交易日。
- 实现：`map_datetime_to_trade_date(dt, trade_calendar)`，trade_calendar 取行情表中日期集合。

## 4. 手续费与成交量方向
- 开仓手数：多头为正、空头为负；平仓手数符号相反。
- 手续费拆分：`fee_half = 手续费 / 2 (tick)`；货币化：`fee_half * tick_size * size * volume`，开/平各一次。

## 5. 逐日盯市算法
按交易日顺序循环（覆盖最早开仓日至最晚平仓日）：
1. **事件收集**：当日所有开仓（open_date=当日）与平仓事件（cover_date=当日），按时间排序，开仓优先于平仓。
2. **开仓处理**：记录持仓 Lot（方向、数量、开仓价、开仓交易日、size），累加开仓手续费。
3. **平仓处理（FIFO）**：
   - 若 Lot 开于当日：平当日仓盈亏 = `(cover_price - open_price) * direction * size * qty`
   - 若 Lot 开于历史：平历史仓盈亏 = `(cover_price - prev_close) * direction * size * qty`
   - 累加平仓手续费。
4. **持仓盈亏**（日终对未平仓位）：
   - 当日新仓：`(close_price - open_price) * direction * size * qty`
   - 历史仓：`(close_price - prev_close) * direction * size * qty`
5. **资金与净值**：
   - `trade_pnl` = 当日所有平仓盈亏（未扣手续费）
   - `hold_pnl` = 日终持仓盯市盈亏
   - `trade_cost` = 当日开/平手续费总和
   - `total_pnl = trade_pnl + hold_pnl - trade_cost`
   - `cum_pnl` 累计盈亏，`balance` 当日净资产（初始 1,000,000）
   - `return = total_pnl / 昨日 balance`
   - `net = 昨日 net * (1 + return)`
   - `market_value = |净持仓手数| * size * close_price`
6. **持仓表**（收盘时）：
   - 按方向聚合，成本价为加权平均：当日新仓用开仓价，历史仓用昨日收盘价。
   - 列：`date, ticker, drt, cost_price, close_price, number`

## 6. 输出表结构
- `trade`：`Ticker, Open_trade_datetime, Open_trade_price, Open_trade_num, size, open_commission, Close_trade_datetime, Close_trade_price, Close_trade_num, close_commission`（附 `Unnamed: 0` 递增索引）。
- `position`：`date, ticker, drt, cost_price, close_price, number`（多为正、空为负）。
- `balance`：`date, hold_pnl, trade_pnl, trade_cost, total_pnl, market_value, cum_pnl, balance, return, net`（附 `Unnamed: 0`）。

## 7. 目录与代码结构
- `main.py`：CLI，读取输入、运行仿真、输出 CSV 与 Excel。
- `app/`：
  - `trading_day.py`：交易日映射。
  - `data_loader.py`：读取交易/行情数据，兼容中英文表头，计算手续费。
  - `simulator.py`：逐日盯市核心逻辑与 trade 表构建。
- `tests/test_demo.py`：用官方 demo 数据对标示例 Excel（精确到 1e-6 容差）。
- `output/`：运行产物（trade/position/balance/result.xlsx）。
- `auto_git.sh`：后台自动提交脚本（tmux 会话 `autogit` 托管）。

## 8. 使用步骤
```bash
python3 -m pip install -r requirements.txt
python3 main.py \
  --trades 笔试题A/trades_cf.csv \
  --prices 笔试题A/cf2309.csv \
  --output-dir output \
  --initial-balance 1000000
# 单元测试
python3 -m pytest -q
```

## 9. 设计权衡与改进
- 采用 FIFO 处理平仓，满足常见撮合假设；若需 LIFO/加权，可在 `simulator.py` 调整。
- 手续费以 tick 计价再换算货币，保持与题面一致；如有分档费率可注入配置。
- 交易日映射依赖行情日历顺延，覆盖夜盘与周末；如有节假日需确保行情日历完整。
- 当前持仓表成本价对隔夜仓显示为“昨日收盘价”以符合逐日盯市原则；若需展示原始建仓价，可额外输出字段。

## 10. 产出物
- 代码：`app/*.py`, `main.py`, `tests/test_demo.py`, `requirements.txt`, `.gitignore`, `README.md`
- 运行结果：`output/trade.csv`, `output/position.csv`, `output/balance.csv`, `output/result.xlsx`
- 文档：本文件 `docs/TECHNICAL.md`


