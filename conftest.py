"""Root-level pytest configuration.

Ensures project root is in sys.path for imports before test collection.
"""

import sys
from pathlib import Path

# Add project root to sys.path at import time
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
