"""
Cinevora — Streamlit Application Root Entrypoint
Launches the Cinevora cinema discovery platform.
Usage:
    streamlit run streamlit_app.py
    streamlit run frontend/app.py
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from frontend.app import main

if __name__ == "__main__":
    main()
