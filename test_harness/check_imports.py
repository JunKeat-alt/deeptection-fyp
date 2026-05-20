import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

sys.path.insert(0, str(BACKEND))

try:
    import config
    from inference.fusion import fuse_and_decide

    print("✅ Basic imports OK")
    print("✅ fuse_and_decide found")
except Exception as e:
    print("❌ Import failed:")
    print(type(e).__name__, e)