import os
import sys
from models import HabitManager, UserCharacter
from storage import Storage


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header(text: str):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_habit_card(habit, week_progress, idx=None):
    prefix = f"{idx}. " if idx is not None else ""
    print(f"\n{prefix}[+] {habit.title} [{habit.category}]")
    print(f"   Описание: {habit.description}")
    print(f"   Страйк: {habit.current_streak} | Рекорд: {habit.max_streak}")
    print(f"   Расписание: ", end="")
    if habit.schedule_type == "everyday":
        print("Каждый день")
    else:
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        print(", ".join(days[d] for d in habit.schedule_days))
    print("   Неделя: ", end="")
    for date, completed in week_progress:
        day_short = date.strftime("%a")[:2]
        symbol = "[X]" if completed else "[ ]"
        print(f"{day_short}{symbol} ", end="")
    print()


def print_profile(user):
    print_header(f"Профиль: {user.username}")
    print(f"   Уровень: {user.level}")
    print(f"   Опыт: {user.experience} / {user.level * 100} XP")
    print("\n   Навыки:")
    for cat, lvl in user.skills.items():
        bar = "#" * min(lvl, 10) + "." * max(0, 10 - lvl)
        print(f"     {cat}: {lvl} {bar}")


def wait_for_back():
    print("\n" + "-" * 60)
    print("  0 - Вернуться в главное меню")
    while True:
        choice = input("Ваш выбор: ").strip()
        if choice == "0":
            return
        else:
            print("   Ошибка: введите 0 для возврата")


def show_profile_and_habits(manager: HabitManager):
    while True:
        clear_screen()
        print_profile(manager.user)
        if not manager.habits:
            print("\nНет привычек. Создайте первую!")
        else:
            print("\n" + "=" * 60)
            print("  СПИСОК ПРИВЫЧЕК")
            print("=" * 60)
            for habit in manager.habits:
                week = manager.get_weekly_progress(habit)
                print_habit_card(habit, week)
        print("\n" + "-" * 60)
        print("  0 - Вернуться в главное меню")
        choice = input("Ваш выбор: ").strip()
        if choice == "0":
            return


def complete_habit(manager: HabitManager):
    while True:
        clear_screen()
        print_header("Отметить выполнение")
        due_habits = manager.get_habits_for_today()
        if not due_habits:
            print("\nНа сегодня все привычки выполнены или нет задач!")
            wait_for_back()
            return
        print("\nПривычки, которые нужно выполнить сегодня:")
        for i, habit in enumerate(due_habits, 1):
            print(f"  {i}. {habit.title} [{habit.category}] - {habit.description}")
        print("\n" + "-" * 60)
        print("  Введите номер привычки для выполнения")
        print("  0 - Вернуться в главное меню")
        try:
            choice = input("Ваш выбор: ").strip()
            if choice == "0":
                return
            idx = int(choice) - 1
            if idx < 0 or idx >= len(due_habits):
                print("Ошибка: неверный номер!")
                wait_for_back()
                return
            habit = due_habits[idx]
            result = manager.complete_habit(habit.title)
            if result["success"]:
                print(f"\n[OK] Привычка «{habit.title}» выполнена!")
                print(f"   +{result['xp_gained']} XP получено!")
                if result["new_record"]:
                    print("   [НОВЫЙ РЕКОРД]")
                if result["level_up"]:
                    print(f"\n[LEVEL UP] Теперь вы {result['new_level']} уровень!")
                print(f"   Текущий страйк: {result['new_streak']}")
            else:
                print(f"\n[ОШИБКА] {result['error']}")
            wait_for_back()
            return
        except ValueError:
            print("Ошибка: введите число!")
            wait_for_back()
            return
        except Exception as e:
            print(f"Ошибка: {e}")
            wait_for_back()
            return


def create_habit(manager: HabitManager):
    while True:
        clear_screen()
        print_header("Создать привычку")
        print("  0 - Вернуться в главное меню")
        try:
            title = input("Название (или 0 для выхода): ").strip()
            if title == "0":
                return
            if not title:
                print("Ошибка: название не может быть пустым!")
                wait_for_back()
                return
            description = input("Описание (или 0 для выхода): ").strip()
            if description == "0":
                return
            if not description:
                print("Ошибка: описание не может быть пустым!")
                wait_for_back()
                return
            print("\nКатегории: 1. Спорт  2. Интеллект  3. Быт")
            cat_choice = input("Выберите категорию (1-3) (или 0 для выхода): ").strip()
            if cat_choice == "0":
                return
            categories = {"1": "Спорт", "2": "Интеллект", "3": "Быт"}
            category = categories.get(cat_choice)
            if category is None:
                print("Ошибка: неверная категория!")
                wait_for_back()
                return
            print("\nРасписание:")
            print("  1. Каждый день")
            print("  2. По выбранным дням недели")
            sched_choice = input("Выберите (1-2) (или 0 для выхода): ").strip()
            if sched_choice == "0":
                return
            if sched_choice == "1":
                schedule_type = "everyday"
                schedule_days = []
            elif sched_choice == "2":
                schedule_type = "custom"
                days_map = {
                    "1": 0, "2": 1, "3": 2, "4": 3,
                    "5": 4, "6": 5, "7": 6,
                }
                print("\nВыберите дни (через пробел, например: 1 3 5):")
                print("  1-Пн, 2-Вт, 3-Ср, 4-Чт, 5-Пт, 6-Сб, 7-Вс")
                print("  (или 0 для выхода)")
                days_input = input("Дни: ").strip().split()
                if days_input == ["0"]:
                    return
                schedule_days = []
                for d in days_input:
                    if d in days_map:
                        schedule_days.append(days_map[d])
                if not schedule_days:
                    print("Ошибка: не выбрано ни одного дня!")
                    wait_for_back()
                    return
            else:
                print("Ошибка: неверный выбор!")
                wait_for_back()
                return
            manager.add_habit(title, description, category, schedule_type, schedule_days)
            print(f"\n[OK] Привычка «{title}» создана!")
            wait_for_back()
            return
        except Exception as e:
            print(f"Ошибка: {e}")
            wait_for_back()
            return


def delete_habit(manager: HabitManager):
    while True:
        clear_screen()
        print_header("Удалить привычку")
        if not manager.habits:
            print("Нет привычек для удаления.")
            wait_for_back()
            return
        for i, habit in enumerate(manager.habits, 1):
            print(f"  {i}. {habit.title} [{habit.category}]")
        print("\n" + "-" * 60)
        print("  Введите номер привычки для удаления")
        print("  0 - Вернуться в главное меню")
        try:
            choice = input("Ваш выбор: ").strip()
            if choice == "0":
                return
            idx = int(choice) - 1
            if idx < 0 or idx >= len(manager.habits):
                print("Ошибка: неверный номер!")
                wait_for_back()
                return
            habit = manager.habits[idx]
            print(f"\nУдалить «{habit.title}»?")
            print("  1. Да")
            print("  2. Нет (вернуться)")
            confirm = input("Ваш выбор: ").strip()
            if confirm == "1":
                manager.delete_habit(habit.title)
                print(f"[OK] Привычка «{habit.title}» удалена.")
                wait_for_back()
                return
            else:
                print("Отменено.")
                wait_for_back()
                return
        except ValueError:
            print("Ошибка: введите число!")
            wait_for_back()
            return
        except Exception as e:
            print(f"Ошибка: {e}")
            wait_for_back()
            return


def main_menu(manager: HabitManager):
    storage = Storage()
    while True:
        clear_screen()
        print_header("HabitHero - Трекер привычек")
        print(f"\nПользователь: {manager.user.username} | Ур. {manager.user.level} | "
              f"XP: {manager.user.experience}/{manager.user.level * 100}")
        logs = manager.update_streaks_and_penalties()
        for log in logs:
            print(f"\n[ВНИМАНИЕ] {log}")
        print("\nМЕНЮ:")
        print("  1. Мой профиль и привычки")
        print("  2. Отметить выполнение")
        print("  3. Создать новую привычку")
        print("  4. Удалить привычку")
        print("  5. Выход и сохранение")
        print("\n" + "-" * 60)
        choice = input("Выберите действие (1-5): ").strip()
        try:
            if choice == "1":
                show_profile_and_habits(manager)
            elif choice == "2":
                complete_habit(manager)
            elif choice == "3":
                create_habit(manager)
            elif choice == "4":
                delete_habit(manager)
            elif choice == "5":
                storage.save(manager)
                print("\n[OK] Данные сохранены. До встречи!")
                sys.exit(0)
            else:
                print("\nОшибка: неверный выбор! Введите 1-5")
                input("\nНажмите Enter, чтобы продолжить...")
        except KeyboardInterrupt:
            print("\n\nВыход...")
            storage.save(manager)
            sys.exit(0)
        except Exception as e:
            print(f"\nОшибка: {e}")
            input("\nНажмите Enter, чтобы продолжить...")


def main():
    storage = Storage()
    manager = storage.load()
    if manager is None:
        clear_screen()
        print_header("Добро пожаловать в HabitHero!")
        print("\nСоздание нового профиля...")
        username = input("Введите ваше имя: ").strip() or "Hero"
        user = UserCharacter(username=username)
        manager = HabitManager(user)
        print(f"\nПривет, {username}! Начнём формировать привычки?")
        print("\nНажмите Enter, чтобы продолжить...")
        input()
    main_menu(manager)


if __name__ == "__main__":
    main()