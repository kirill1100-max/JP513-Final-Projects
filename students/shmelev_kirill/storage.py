import json
import os
from typing import Optional
from models import HabitManager


class Storage:
    def __init__(self, filename: str = "habits.json"):
        self.filename = filename

    def save(self, manager: HabitManager) -> None:
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(manager.to_dict(), f, ensure_ascii=False, indent=4)

    def load(self) -> Optional[HabitManager]:
        if not os.path.exists(self.filename):
            return None
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    os.remove(self.filename)
                    return None
                data = json.loads(content)
                return HabitManager.from_dict(data)
        except json.JSONDecodeError:
            os.remove(self.filename)
            return None
        except Exception:
            os.remove(self.filename)
            return None