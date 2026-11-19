#!/usr/bin/env bash
# 一键安装 zh-nutrition-humanizer 到某个 harness 的技能目录。
#
#   ./bootstrap.sh                      # 默认装到 ~/.claude/skills
#   ./bootstrap.sh --harness dsh        # 装到 ~/.dsh/skills
#   ./bootstrap.sh --dir /some/skills   # 自定义目录
#   ./bootstrap.sh --harness zcode --copy   # 复制而不是软链
#
# 脚本做三件事：放进技能目录、跑自检、告诉你怎么验证。
set -euo pipefail

REPO="https://github.com/ChemistryBus/zh-nutrition-humanizer.git"
NAME="zh-nutrition-humanizer"
HARNESS="claude"
DIR=""
COPY=0

while [ $# -gt 0 ]; do
  case "$1" in
    --harness) HARNESS="$2"; shift 2 ;;
    --dir) DIR="$2"; shift 2 ;;
    --copy) COPY=1; shift ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "未知参数：$1"; exit 2 ;;
  esac
done

if [ -z "$DIR" ]; then
  case "$HARNESS" in
    claude)   DIR="$HOME/.claude/skills" ;;
    codex)    DIR="$HOME/.codex/skills" ;;
    dsh)      DIR="$HOME/.dsh/skills" ;;
    zcode)    DIR="$HOME/.zcode/skills" ;;
    minimax)  DIR="$HOME/.agents/skills" ;;
    workbuddy) DIR="$HOME/.workbuddy/skills" ;;
    kimi)     DIR="$HOME/.kimi/skills" ;;
    *) echo "未知 harness：$HARNESS（可选 claude/codex/dsh/zcode/minimax/workbuddy/kimi）"; exit 2 ;;
  esac
fi

TARGET="$DIR/$NAME"
mkdir -p "$DIR"

SRC="$(cd "$(dirname "$0")" 2>/dev/null && pwd || true)"
LOCAL=0
if [ -n "$SRC" ] && [ -f "$SRC/SKILL.md" ] && [ -d "$SRC/.git" ]; then LOCAL=1; fi

if [ -e "$TARGET" ] || [ -L "$TARGET" ]; then
  echo "已存在：$TARGET"
  if [ -d "$TARGET/.git" ]; then
    echo "→ git pull --ff-only"
    git -C "$TARGET" pull --ff-only || echo "（拉取失败，保留现有版本）"
  else
    echo "→ 保留现有目录，不覆盖"
  fi
elif [ "$LOCAL" -eq 1 ]; then
  if [ "$COPY" -eq 1 ]; then
    echo "→ 复制 $SRC 到 $TARGET"
    cp -R "$SRC" "$TARGET"
  else
    echo "→ 软链 $SRC 到 $TARGET"
    ln -s "$SRC" "$TARGET"
  fi
else
  echo "→ clone 到 $TARGET"
  git clone --depth 1 "$REPO" "$TARGET"
fi

echo
echo "自检："
python3 "$TARGET/scripts/doctor.py" --ci || true

cat <<MSG

装好了。下一步：
  1. 重启对应的 harness 会话（技能在启动时扫描）；
  2. 让 agent 说一句「用 zh-nutrition-humanizer 检查这篇稿子」验证；
  3. 想先看效果：python3 "$TARGET/scripts/check.py" "$TARGET/examples/before.md"
MSG
