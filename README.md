# 交叉科技量化交易笔试题（CF2309）

## 项目说明
- 数据来源：`trades_cf.csv`（交易记录）、`cf2309.csv`（日线行情），示例输出在 `demo/三表输出结果示例.xlsx`。
- 目标：按题目描述生成 `trade`、`position`、`balance` 三张表，采用逐日盯市逻辑，初始资金 1,000,000。
- 环境：Python 3.10，依赖 `pandas`、`openpyxl`、`PyPDF2`。

## 使用方式
1. 安装依赖（已提供 `requirements.txt`）：  
   `python3 -m pip install -r requirements.txt`
2. 运行主程序（默认读 `笔试题A/` 下原始输入，输出到 `output/`）：  
   `python3 main.py`  
   自定义参数：`python3 main.py --trades <path> --prices <path> --output-dir <dir> --initial-balance 1000000`
3. 结果将写入：`output/trade.csv`、`output/position.csv`、`output/balance.csv`，并在 `output/result.xlsx` 汇总三张表。
4. 运行单元测试（使用官方 demo 数据对标示例 Excel）：  
   `python3 -m pytest -q`

## 当前进度
- 完成：数据解压、依赖安装、Git 初始化与 SSH 配置、Auto-Git 后台运行（tmux 会话 `autogit`，日志 `auto_git.log`）。
- 完成：核心逻辑与 CLI，demo 用例对标示例 Excel 的单元测试。

## Auto-Git 脚本
- 位置：`auto_git.sh`，默认每 1800s 检查变更并提交/推送。
- 配置参数：`INTERVAL`、`BRANCH`、`REMOTE`、`LOG_FILE`（可环境变量覆盖）。
- 运行（已由 tmux 托管）：`tmux attach -t autogit` 查看，`Ctrl+b` `d` 挂起。


