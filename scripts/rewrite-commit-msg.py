#!/usr/bin/env python3
import sys, re
msg = sys.stdin.read()
msg = re.sub(r"\n?Co-authored-by:\s*Cursor\s*<[^>]+>\s*\n?", "\n", msg, flags=re.IGNORECASE)
msg = re.sub(r"\n?Made-with:\s*Cursor\s*\n?", "\n", msg, flags=re.IGNORECASE)
msg = re.sub(r"\n{3,}", "\n\n", msg).strip()
print(msg + "\n" if msg else "")
