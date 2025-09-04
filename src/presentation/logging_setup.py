import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    force=True,
)
logger = logging.getLogger("sadfi.ui")

def file_stat(path_str: str) -> str:
    p = Path(path_str)
    try:
        if not p.exists():
            return f"{path_str} (não encontrado)"
        size_kb = p.stat().st_size / 1024
        mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        return f"{path_str} ({size_kb:.1f} KB, mtime {mtime})"
    except Exception as e:
        return f"{path_str} (erro ao inspecionar: {e})"
