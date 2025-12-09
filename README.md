# 交叉科技量化交易笔试题（CF2309）

## 项目说明
- 数据来源：`trades_cf.csv`（交易记录）、`cf2309.csv`（日线行情），示例输出在 `demo/三表输出结果示例.xlsx`。
- 目标：按题目描述生成 `trade`、`position`、`balance` 三张表，采用逐日盯市逻辑，初始资金 1,000,000 万（题面给定）。
- 环境：Python 3.10，依赖 `pandas`、`openpyxl`、`PyPDF2`。

## 当前进度
- 已完成环境准备：解压数据、安装依赖、初始化 Git、配置 SSH、公钥已生成（等待远端绑定后推送已测试）。
- 已创建自动提交脚本：`auto_git.sh`（tmux 会话 `autogit` 中后台运行，日志 `auto_git.log`）。
- 正在分析题目需求与数据结构，尚未编写核心计算代码。

## 使用指南（草稿）
1. 激活虚拟环境（如有）或直接使用系统 Python 3.10。
2. 安装依赖：`python3 -m pip install -r requirements.txt`（后续补充）。
3. 运行主程序（待实现）：`python3 main.py`。
4. 结果输出：生成三表（CSV/Excel），格式参考 `demo/三表输出结果示例.xlsx`。

## Auto-Git 脚本
- 位置：`auto_git.sh`，默认每 1800s 检查变更并提交/推送。
- 配置参数：`INTERVAL`、`BRANCH`、`REMOTE`、`LOG_FILE`（可环境变量覆盖）。
- 运行（已由 tmux 托管）：`tmux attach -t autogit` 查看，`Ctrl+b` `d` 挂起。


