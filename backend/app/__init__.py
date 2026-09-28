# DrishtiGIS backend package
import sys
from pathlib import Path

# Ensure both repository root and backend directory are on sys.path
# so imports like 'from app...' and 'from backend.app...' resolve seamlessly
# regardless of whether the process was started from the repo root or backend/.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent

for _p in (str(_REPO_ROOT), str(_BACKEND_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
