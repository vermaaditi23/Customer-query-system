import os
import tempfile
from pathlib import Path

PORT = int(os.getenv("PORT", "7860"))
SESSION_TTL_MINUTES = int(os.getenv("SESSION_TTL_MINUTES", "20"))
MAX_FAILED_VERIFY = int(os.getenv("MAX_FAILED_VERIFY", "5"))
LOCKOUT_MINUTES = int(os.getenv("LOCKOUT_MINUTES", "5"))

CHAT_LIMIT_PER_MIN = int(os.getenv("CHAT_LIMIT_PER_MIN", "60"))
VERIFY_LIMIT_PER_10MIN = int(os.getenv("VERIFY_LIMIT_PER_10MIN", "10"))

# SQLite file lives in the system temp folder
DB_PATH = Path(tempfile.gettempdir()) / "customer_query_app.db"


def find_csv_dir() -> Path:
    """Works locally (project/data/csv) and in Docker (/app/data/csv)."""
    env = os.getenv("DATA_DIR")
    here = Path(__file__).resolve()
    candidates = [Path(env)] if env else []
    candidates += [here.parents[1] / "data" / "csv", here.parents[2] / "data" / "csv"]
    for c in candidates:
        if (c / "orders.csv").exists():
            return c
    raise FileNotFoundError("Could not find data/csv with the dataset files")