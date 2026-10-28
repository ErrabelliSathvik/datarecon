
import json
from pathlib import Path

from datarecon.run_history import get_runs

database_path = Path("outputs/datarecon.db")

if not database_path.exists():
    print("No run-history database found. Run the pipeline first.")
else:
    runs = get_runs(str(database_path))
    print(json.dumps(runs, indent=2))
