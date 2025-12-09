#!/usr/bin/env bash
# 自动增量提交/推送脚本，需在已初始化的 Git 仓库中运行。
# 可通过环境变量调整行为：
#   INTERVAL: 循环间隔（秒），默认 1800
#   BRANCH  : 推送分支名，默认 main
#   REMOTE  : 远端名，默认 origin
#   LOG_FILE: 日志文件路径，默认 auto_git.log（位于脚本所在目录）

set -euo pipefail

INTERVAL="${INTERVAL:-1800}"
BRANCH="${BRANCH:-main}"
REMOTE="${REMOTE:-origin}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${LOG_FILE:-${SCRIPT_DIR}/auto_git.log}"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" | tee -a "$LOG_FILE"
}

cd "$SCRIPT_DIR"

while true; do
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    log "未检测到 Git 仓库，暂停本轮，${INTERVAL}s 后重试。"
    sleep "$INTERVAL"
    continue
  fi

  if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
    log "远端 '$REMOTE' 未配置，跳过推送，${INTERVAL}s 后重试。"
    sleep "$INTERVAL"
    continue
  fi

  # 检查是否有变更（含未跟踪文件）
  if git status --porcelain | grep -q .; then
    git add -A
    if git commit -m "auto-checkpoint $(date '+%Y-%m-%d %H:%M:%S')" >/dev/null 2>&1; then
      log "已提交本地变更。"
    else
      log "无可提交内容（可能是全部被忽略）。"
    fi

    if git push "$REMOTE" "$BRANCH" >/dev/null 2>&1; then
      log "推送成功 -> ${REMOTE}/${BRANCH}"
    else
      log "推送失败，请稍后检查网络/权限。"
    fi
  else
    log "无变更，跳过提交与推送。"
  fi

  sleep "$INTERVAL"
done

