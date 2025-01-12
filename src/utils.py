from datetime import datetime

import pandas as pd
from pandas import DataFrame


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


def filter_dataframe(df: DataFrame, colname: dict, operator: str = "AND") -> pd.DataFrame:
    """
    Функция принимает датафрейм с транзакциями, и фильтрует его по заданным условиям
    Args:
        df (DataFrame): Исходный DataFrame.
        colname (dict): Словарь фильтров, где ключи — названия колонок, а значения — значения или функции фильтрации.
        operator (str): 'AND' или 'OR', как объединять условия.

    Returns:
        DataFrame: Отфильтрованный DataFrame.
    """

    if operator not in ("AND", "OR"):
        raise ValueError("Условие должно быть AND или OR")

    conditions = []
    for key, condition in colname.items():
        if callable(condition):
            conditions.append(condition(df[key]))
        else:
            conditions.append(df[key] == condition)
    combined_conditions = conditions[0]
    for condition in conditions[1:]:
        if operator == "AND":
            combined_conditions &= condition
        else:
            combined_conditions |= condition
    filtered_df = df[combined_conditions]
    # Убедимся, что filtered_df действительно типа DataFrame
    assert isinstance(filtered_df, DataFrame)

    return filtered_df


if __name__ == "__main__":
    print(greetings())

    df = get_data("data/operations.xlsx")
    example_df = df.iloc[:10]

    colname = {
        "Валюта операции" : "CNY",
        "Статус" : "OK",
        "Сумма операции" : lambda x: x < 0
    }

    print(filter_dataframe(df, colname, "AND"))
