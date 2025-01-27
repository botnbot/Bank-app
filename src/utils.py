import re
from datetime import datetime
from typing import Any

import pandas as pd


def greetings() -> str:
    """Функция возвращает приветствие в зависимости от времени суток"""
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
    """Функция принимает на вход путь к файлу .xlsx и возвращает DataFrame"""
    df = pd.read_excel(path)
    return df


def filter_dataframe(df: pd.DataFrame, filtr_conditions: dict, operator: str = "AND") -> Any:
    """
    Функция принимает датафрейм с транзакциями, и фильтрует его по заданным условиям.
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
