import re
from datetime import datetime
from typing import Any, Optional

import pandas as pd


def greetings() -> str:
    """
    Функция возвращает приветствие в зависимости от времени суток
    """
    time = datetime.now().hour
    if 4 < time <= 10:
        return "Доброе утро!"
    elif 10 < time <= 17:
        return "Добрый день!"
    elif 17 < time <= 23:
        return "Добрый вечер!"
    else:
        return "Доброй ночи!"


def get_data(path: str) -> pd.DataFrame:
    """
    Функция принимает на вход путь к файлу .xlsx в виде строки и возвращает DataFrame с транзакциями
         Args:
        str: путь к файлу
        Returns:
        pd.DataFrame: DataFrame."""
    df = pd.read_excel(path)
    return df


def filter_dataframe(df: pd.DataFrame, filtr_conditions: dict, operator: str = "AND") -> Any:
    """
    Функция принимает DataFrame с транзакциями, и фильтрует его по заданным условиям.
    """
    if operator not in ("AND", "OR"):
        raise ValueError("Логический оператор должен быть строкой AND или OR")

    if not filtr_conditions:
        return df

    # Проверяем, что все ключи есть в столбцах DataFrame
    missing_keys = [key for key in filtr_conditions if key not in df.columns]
    if missing_keys:
        raise KeyError(f"Столбцы {missing_keys} отсутствуют в DataFrame")

    conditions = []
    for key, condition in filtr_conditions.items():
        if callable(condition):
            # Если передана функция, применяем её
            conditions.append(condition(df[key]))
        elif isinstance(condition, re.Pattern):
            # Если передано регулярное выражение, применяем его
            conditions.append(df[key].apply(lambda x: bool(condition.match(str(x)))))
        else:
            # Если передано значение, проверяем равенство
            conditions.append(df[key] == condition)

    combined_conditions = conditions[0]
    for condition in conditions[1:]:
        if operator == "AND":
            combined_conditions &= condition
        else:
            combined_conditions |= condition

    filtered_df = df[combined_conditions]
    return filtered_df


def get_date() -> Optional[str]:
    """
    Функция, запрашивающая у пользователя дату для передачи в функцию.
    Возвращает дату в формате "YYYY-MM-DD HH:MM:SS".
    Если ввод пустой, возвращает текущую дату.
    """
    while True:
        try:
            date_input: Optional[str] = input(
                "Введите строку с датой и временем в формате YYYY-MM-DD HH:MM:SS "
                "в диапазоне с 2018-01-01 по 2021-12-31, "
                "или нажмите Enter для использования текущей даты: "
            ).strip()

            # Проверяем, если ввод пустой
            if not date_input:
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Возвращаем текущую дату

            # Пробуем преобразовать введённую дату
            date = datetime.strptime(date_input, "%Y-%m-%d %H:%M:%S")

            break
        except ValueError as e:
            print(f"Не удалось получить дату: {e}. Попробуйте снова.")
    return date.strftime("%Y-%m-%d %H:%M:%S")  # Возвращаем дату в нужном формате
