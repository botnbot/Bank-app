import json
import os
from datetime import datetime
from typing import Any

import src.reports
import src.services
import src.views
from config import ROOT_PATH
from src.reports import expenses_by_days_of_the_week, expenses_by_working_day, get_report_by_category
from src.services import (find_money_transfers_from_individuals, investment_bank, mobile_phone_search,
                          profitable_cashback, simple_search)
from src.utils import get_data, get_date
from src.views import events, views

categories = {
    "w": (
        "Веб-страницы",
        {
            "1": "Главная",
            "2": "События",
        },
    ),
    "s": (
        "Сервисы",
        {
            "1": "Выгодные категории кешбэка",
            "2": "Инвесткопилка",
            "3": "Простой поиск",
            "4": "Поиск по телефонным номерам",
            "5": "Поиск переводов физ. лицам",
        },
    ),
    "r": (
        "Отчеты",
        {
            "1": "Траты по категории",
            "2": "Траты по дням недели",
            "3": "Траты в рабочий/выходной день",
        },
    ),
}


def menu(prompt: str, options: set) -> str:
    """Обрабатывает ввод пользователя и проверяет корректность выбора."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in options:
            return choice
        print("Некорректный ввод, попробуйте снова.")


def handle_web_pages(option: str) -> Any:
    """Обрабатывает раздел 'Веб-страницы'."""
    match option:
        case "1":
            optional_date = get_date()
            result = views(optional_date)
            # print(result)
            return result
        case "2":
            while True:
                period = (
                    input(
                        "Введите период(по умолчанию - месяц):\n"
                        "W — неделя,\nM — месяц(можно ничего не вводить),\nY — год,\nALL — все данные до даты\n"
                        "q — выход из раздела\n"
                    )
                    .strip()
                    .upper()
                )
                print(f"Вы выбрали период {period}")
                if period == "q":
                    print('Выход из раздела "События".')
                    return
                optional_date = get_date()
                result = events(optional_date, period)
                # print(result)
                return result


def handle_services(option: str) -> Any:
    """Обрабатывает раздел 'Сервисы'."""
    match option:
        case "1":
            data_path = os.path.join(ROOT_PATH, "data/operations.xlsx")
            data = get_data(data_path)
            year = input("Введите номер года: ").strip()
            month = input("Введите номер месяца: ").strip()
            result = profitable_cashback(data, year, month)
            # print(result)
            return result
        case "2":
            df = get_data()
            transactions = df.to_dict("records")
            optional_date = get_date()
            date_ = datetime.strptime(optional_date, "%Y-%m-%d %H:%M:%S")
            date = datetime.strftime(date_, "%Y-%m")
            limit = None
            while limit not in range(10, 101):
                limit = float(input("Введите предел округления в диапазоне от 10 до 100  "))
            result = investment_bank(date, transactions, limit)
            # print(f"Сумма для «Инвесткопилки»: {result}")
            return result
        case "3":
            search = input("Введите строку для поиска: ")
            result = simple_search(search)
            # print(result)
            return result
        case "4":
            result = mobile_phone_search()
            # print(result)
            return result
        case "5":
            data_path = os.path.join(ROOT_PATH, "data/operations.xlsx")
            result = find_money_transfers_from_individuals(data_path)
            # money_transfers = json.loads(result)
            # print(json.dumps(money_transfers, ensure_ascii=False, indent=2))
            return result


def handle_reports(option: str) -> Any:
    """Обрабатывает раздел 'Отчеты'."""
    match option:
        case "1":
            exp_category_list = [
                "Супермаркеты",
                "Различные товары",
                "Переводы",
                "Каршеринг",
                "Дом и ремонт",
                "Фастфуд",
                "Аптеки",
            ]

            while True:
                category = input(
                    "Введите категорию трат из списка:\n"
                    + "\n".join(exp_category_list)
                    + "\nq - Завершение программы\n"
                ).strip()
                if category.lower() == "q":
                    print("Программа завершена.")
                    return
                elif category in exp_category_list:
                    transactions = get_data()
                    date = get_date()
                    result = get_report_by_category(transactions, category, date)
                    # print(json.dumps(result, indent=4, ensure_ascii=False))
                    return result
                print("Некорректная категория. Попробуйте снова.")
        case "2":
            date = get_date()
            transactions = get_data()
            result = expenses_by_days_of_the_week(transactions, date)
            # print(json.dumps(result, ensure_ascii=False, indent=1))
            return result
        case "3":
            result = expenses_by_working_day(get_data(), get_date())
            # print(json.dumps(result, ensure_ascii=False, indent=1))
            return result


while True:
    first_level = menu(
        "Выберите категорию:\n" "w - Веб-страницы\n" "s - Сервисы\n" "r - Отчеты\n" "q - Завершение программы\n",
        {"w", "s", "r", "q"},
    )

    if first_level == "q":
        print("Программа завершена.")
        break

    category_name, subcategories = categories[first_level]
    print(f"Вы выбрали категорию: {category_name}")

    second_level = menu(
        "Выберите подкатегорию:\n"
        + "\n".join(f"{k} - {v}" for k, v in subcategories.items())
        + "\nq - Завершение программы\n",
        set(subcategories.keys()) | {"q"},
    )

    if second_level == "q":
        print("Программа завершена.")
        break

    print(f"Вы выбрали: {subcategories[second_level]}")

    try:
        match first_level:
            case "w":
                handle_web_pages(second_level)
            case "s":
                handle_services(second_level)
            case "r":
                handle_reports(second_level)

    except ValueError as e:
        error_message = f"Ошибка {e} в разделе '{subcategories[second_level]}'"
        match first_level:
            case "w":
                src.views.loger.error(error_message)
            case "s":
                src.services.loger.error(error_message)
            case "r":
                src.reports.loger.error(error_message)
