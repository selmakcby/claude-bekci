"""Denetçi kayıtları: <proje>/.denetci/kayit.jsonl. Sırrın kendisi asla yazılmaz, sadece kural adı."""
import json
from datetime import datetime, timezone
from pathlib import Path


def yaz(cwd, olay):
    if not cwd:
        return
    try:
        klasor = Path(cwd) / ".denetci"
        klasor.mkdir(exist_ok=True)
        satir = {"zaman": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"), **olay}
        with open(klasor / "kayit.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(satir, ensure_ascii=False) + "\n")
    except OSError:
        pass  # kayıt yazılamadı diye ajan durdurulmaz
