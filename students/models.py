import datetime
from typing import List, Optional, Dict, Any, Tuple


class UserCharacter:
    def __init__(self, username: str = "Hero", level: int = 1, experience: int = 0,
                 skills: Optional[Dict[str, int]] = None):
        self.username = username
        self.level = level
        self.experience = experience
        self.skills = skills or {"Спорт": 1, "Интеллект": 1, "Быт": 1}

    def add_xp(self, amount: int, category: str) -> bool:
        self.experience += amount
        if category in self.skills:
            self.skills[category] += 1
        level_up = False
        while self.experience >= self.level * 100:
            self.experience -= self.level * 100
            self.level += 1
            level_up = True
        return level_up

    def deduct_xp(self, amount: int) -> None:
        self.experience = max(0, self.experience - amount)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "level": self.level,
            "experience": self.experience,
            "skills": self.skills,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserCharacter":
        return cls(
            username=data["username"],
            level=data["level"],
            experience=data["experience"],
            skills=data.get("skills", {"Спорт": 1, "Интеллект": 1, "Быт": 1}),
        )


class Habit:
    def __init__(
        self,
        title: str,
        description: str,
        category: str,
        schedule_type: str,
        schedule_days: Optional[List[int]] = None,
        creation_date: Optional[datetime.date] = None,
        dates_completed: Optional[List[datetime.date]] = None,
        current_streak: int = 0,
        max_streak: int = 0,
    ):
        self.title = title
        self.description = description
        self.category = category
        self.schedule_type = schedule_type
        self.schedule_days = schedule_days if schedule_days else []
        self.creation_date = creation_date or datetime.date.today()
        self.dates_completed = dates_completed or []
        self.current_streak = current_streak
        self.max_streak = max_streak

    def check_in(self, date: Optional[datetime.date] = None) -> Tuple[bool, bool]:
        if date is None:
            date = datetime.date.today()
        if date in self.dates_completed:
            return False, False
        self.dates_completed.append(date)
        self._recalculate_streak()
        new_record = self.current_streak > self.max_streak
        if new_record:
            self.max_streak = self.current_streak
        return True, new_record

    def _recalculate_streak(self) -> None:
        if not self.dates_completed:
            self.current_streak = 0
            return
        today = datetime.date.today()
        calc_dates = self._get_schedule_dates(
            start_date=self.creation_date,
            end_date=today,
        )
        streak = 0
        for d in reversed(calc_dates):
            if d in self.dates_completed:
                streak += 1
            else:
                break
        self.current_streak = streak

    def _get_schedule_dates(self, start_date: datetime.date, end_date: datetime.date) -> List[datetime.date]:
        dates = []
        current = start_date
        while current <= end_date:
            if self._is_schedule_day(current):
                dates.append(current)
            current += datetime.timedelta(days=1)
        return dates

    def _is_schedule_day(self, date: datetime.date) -> bool:
        if self.schedule_type == "everyday":
            return True
        weekday = date.weekday()
        return weekday in self.schedule_days

    def get_last_schedule_day_before(self, date: datetime.date) -> Optional[datetime.date]:
        current = date - datetime.timedelta(days=1)
        while current >= self.creation_date:
            if self._is_schedule_day(current):
                return current
            current -= datetime.timedelta(days=1)
        return None

    def is_due_today(self) -> bool:
        return self._is_schedule_day(datetime.date.today())

    def is_completed_today(self) -> bool:
        return datetime.date.today() in self.dates_completed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "schedule_type": self.schedule_type,
            "schedule_days": self.schedule_days,
            "creation_date": self.creation_date.isoformat(),
            "current_streak": self.current_streak,
            "max_streak": self.max_streak,
            "dates_completed": [d.isoformat() for d in self.dates_completed],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Habit":
        return cls(
            title=data["title"],
            description=data["description"],
            category=data["category"],
            schedule_type=data["schedule_type"],
            schedule_days=data.get("schedule_days", []),
            creation_date=datetime.date.fromisoformat(data["creation_date"]),
            dates_completed=[datetime.date.fromisoformat(d) for d in data.get("dates_completed", [])],
            current_streak=data.get("current_streak", 0),
            max_streak=data.get("max_streak", 0),
        )


class HabitManager:
    def __init__(self, user: UserCharacter, habits: Optional[List[Habit]] = None):
        self.user = user
        self.habits = habits or []

    def add_habit(
        self,
        title: str,
        description: str,
        category: str,
        schedule_type: str,
        schedule_days: Optional[List[int]] = None,
    ) -> None:
        habit = Habit(
            title=title,
            description=description,
            category=category,
            schedule_type=schedule_type,
            schedule_days=schedule_days,
        )
        self.habits.append(habit)

    def delete_habit(self, title: str) -> bool:
        for i, habit in enumerate(self.habits):
            if habit.title == title:
                del self.habits[i]
                return True
        return False

    def complete_habit(self, title: str) -> Dict[str, Any]:
        habit = self._find_habit(title)
        if habit is None:
            return {"success": False, "error": "Привычка не найдена"}
        if habit.is_completed_today():
            return {"success": False, "error": "Сегодня уже выполнено"}
        if not habit.is_due_today():
            return {"success": False, "error": "Сегодня не расчётный день"}
        completed, new_record = habit.check_in()
        if not completed:
            return {"success": False, "error": "Не удалось отметить"}
        base_xp = 10
        streak_bonus = min(habit.current_streak // 2, 10)
        total_xp = base_xp + streak_bonus
        level_up = self.user.add_xp(total_xp, habit.category)
        return {
            "success": True,
            "habit_title": habit.title,
            "xp_gained": total_xp,
            "new_streak": habit.current_streak,
            "new_record": new_record,
            "level_up": level_up,
            "new_level": self.user.level if level_up else None,
        }

    def update_streaks_and_penalties(self) -> List[str]:
        logs = []
        today = datetime.date.today()
        for habit in self.habits:
            last_due = habit.get_last_schedule_day_before(today)
            if last_due is None:
                continue
            if last_due in habit.dates_completed:
                continue
            if habit.current_streak > 0:
                habit.current_streak = 0
                self.user.deduct_xp(15)
                day_name = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][last_due.weekday()]
                logs.append(
                    f"Привычка «{habit.title}» прервана! "
                    f"Расчётный день ({day_name}) был пропущен. Страйк сброшен!"
                )
        return logs

    def get_habits_for_today(self) -> List[Habit]:
        return [h for h in self.habits if h.is_due_today() and not h.is_completed_today()]

    def get_weekly_progress(self, habit: Habit) -> List[Tuple[datetime.date, bool]]:
        today = datetime.date.today()
        week = []
        for i in range(6, -1, -1):
            day = today - datetime.timedelta(days=i)
            completed = day in habit.dates_completed
            week.append((day, completed))
        return week

    def _find_habit(self, title: str) -> Optional[Habit]:
        for habit in self.habits:
            if habit.title == title:
                return habit
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user": self.user.to_dict(),
            "habits": [h.to_dict() for h in self.habits],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HabitManager":
        user = UserCharacter.from_dict(data["user"])
        habits = [Habit.from_dict(h) for h in data.get("habits", [])]
        return cls(user, habits)