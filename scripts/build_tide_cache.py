import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
from tide import build_cache

base = os.path.join(os.path.dirname(__file__), "..", "pipeline", "tide_source")
out1 = build_cache(os.path.join(base, "recife_2026.pdf"), 2026, "recife_2026.json")
print("OK:", out1)
out2 = build_cache(os.path.join(base, "suape_2026.pdf"), 2026, "suape_2026.json")
print("OK:", out2)
