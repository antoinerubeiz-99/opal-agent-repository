"""Vercel serverless entrypoint.

Vercel's Python runtime serves the ASGI `app` object from files under api/.
All routes are rewritten here (see ../vercel.json), so the FastAPI app in
main.py handles /discovery and /tools/* unchanged.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app  # noqa: E402,F401
