#!/usr/bin/env python3
import subprocess
import sys

cmd = ["alembic", "-c", "alembic.ini", "heads"]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)

heads = [line for line in result.stdout.splitlines() if "(head)" in line]
if len(heads) > 1:
    print("Multiple alembic heads detected:")
    for line in heads:
        print(line)
    sys.exit(1)

sys.exit(0)
