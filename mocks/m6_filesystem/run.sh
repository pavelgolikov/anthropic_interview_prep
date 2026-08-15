#!/usr/bin/env bash
# Usage:
#   ./run.sh          run every level against solution.py
#   ./run.sh 3        run level 3 only
#   ./run.sh 3 --ref  run level 3 against the reference solution (post-mortem only)
set -u
cd "$(dirname "$0")"
NAME=$(basename "$PWD")
LEVEL=""
USE_REF=0
for arg in "$@"; do
  case "$arg" in
    --ref) USE_REF=1 ;;
    [1-5]) LEVEL="$arg" ;;
    *) echo "usage: ./run.sh [1-5] [--ref]" >&2; exit 2 ;;
  esac
done

WORKDIR="$PWD"
if [ "$USE_REF" = 1 ]; then
  WORKDIR=$(mktemp -d)
  cp "../../reference/$NAME.py" "$WORKDIR/solution.py"
  cp test_solution.py "$WORKDIR/"
fi

TARGET="test_solution"
[ -n "$LEVEL" ] && TARGET="test_solution.TestLevel$LEVEL"

cd "$WORKDIR" && python3 -m unittest "$TARGET" -v
