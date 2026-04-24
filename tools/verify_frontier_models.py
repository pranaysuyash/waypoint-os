import sys
import os
from pathlib import Path

# Add spine-api to path
sys.path.append(os.getcwd())

try:
    from models import (
        Agency, User, Membership, WorkspaceCode,
        GhostWorkflow, EmotionalStateLog, IntelligencePoolRecord, LegacyAspiration
    )
    print("✅ All models imported successfully.")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
