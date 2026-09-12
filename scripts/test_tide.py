import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
from tide import TideTable
from datetime import datetime, timezone

t = TideTable(os.path.join(os.path.dirname(__file__), "..", "pipeline", "tide_data", "recife_2026.json"))

# 12/set/2026 04:23 local = 07:23 UTC -> deve ser baixa-mar (~0.13m, do dado que ja vimos)
tests = [
    datetime(2026, 9, 12, 7, 23, tzinfo=timezone.utc),   # baixamar exata (recife dia12: 1046 0.13 local -> 1346 utc, ops let's just test the extrema time)
    datetime(2026, 9, 12, 6, 0, tzinfo=timezone.utc),
    datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc),
    datetime(2026, 9, 12, 18, 0, tzinfo=timezone.utc),
]
for dt in tests:
    print(dt, "->", round(t.height_at(dt), 2), "m")
