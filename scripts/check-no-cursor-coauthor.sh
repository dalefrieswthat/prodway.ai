#!/usr/bin/env bash
# Reject commit if message contains Cursor co-author trailer (project policy).
msgfile="${1:?}"
if grep -q "Co-authored-by: Cursor" "$msgfile" 2>/dev/null; then
  echo "Commit rejected: remove 'Co-authored-by: Cursor' trailer (see CLAUDE.md / .cursor/rules)."
  exit 1
fi
exit 0
