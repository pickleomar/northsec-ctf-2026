from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import app


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=False, threaded=True)
