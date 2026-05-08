from pathlib import Path

# Корень проекта -- родитель папки core (т.е. туда, где лежит daemon.py, cli.py и т.д.)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Вся эфемерная runtime-информация демона -- внутри проекта
STATE_DIR = PROJECT_ROOT / ".rag"
PORT_FILE = STATE_DIR / "daemon.port"
PID_FILE = STATE_DIR / "daemon.pid"
