import re
from datetime import datetime
from typing import Any

import pandas as pd
from pandas import DataFrame


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


def get_date() -> str:
    """
    Функция, запрашивающая у пользователя дату для передачи в функцию.
    Возвращает дату в формате "YYYY-MM-DD HH:MM:SS".
    Если ввод пустой, возвращает текущую дату.
    """
    while True:
        try:
            date_input: str = input(
                "Введите строку с датой и временем в формате YYYY-MM-DD HH:MM:SS "
                "в диапазоне с 2018-01-01 по 2021-12-31, "
                "или нажмите Enter для использования текущей даты: "
            ).strip()

            if not date_input:
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            date = datetime.strptime(date_input, "%Y-%m-%d %H:%M:%S")
            return date.strftime("%Y-%m-%d %H:%M:%S")

        except ValueError as e:
            print(f"Не удалось получить дату: {e}. Попробуйте снова.")


def get_df_for_current_period(date: str, df: DataFrame, period_type: str = "M") -> Any:
    """
    Возвращает транзакции за текущий период.

    Функция принимает DataFrame со всеми транзакциями и фильтрует его, оставляя только операции,
    которые произошли в пределах заданного периода.

    Args:
        df (DataFrame): Исходный DataFrame с транзакциями. Должен содержать столбец "Дата операции".
        date (str): Строка с датой и временем в формате YYYY-MM-DD HH:MM:SS для определения заданного периода.
        Если не передана, используется текущая дата.
        period_type (str): Диапазон данных. По умолчанию диапазон равен одному месяцу
         (с начала месяца, на который выпадает дата, по саму дату).
         Возможные значения параметра:
         W — неделя, на которую приходится дата;
         M — месяц, на который приходится дата;
         Y — год, на который приходится дата;
         ALL — все данные до указанной даты.

    Returns:
        DataFrame: Отфильтрованный DataFrame с транзакциями за текущий месяц.

    Raises:
        ValueError: Если в DataFrame отсутствует столбец "Дата операции".
    """

    parsed_date = pd.to_datetime(date, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    if pd.isna(parsed_date):
        raise ValueError("Ошибка: передана некорректная дата! Запустите с корректными параметрами.")
    # Преобразуем столбец "Дата операции" в datetime
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce", dayfirst=True)

    # Извлекаем текущую неделю, месяц и год
    current_week = parsed_date.isocalendar().week
    current_month = parsed_date.month
    current_year = parsed_date.year
    # Получение операций за текущий период
    if period_type == "W":

        current_period_df = filter_dataframe(
            df,
            {
                "Дата операции": lambda dates: (dates <= parsed_date)
                & (dates.dt.year == current_year)
                & (dates.dt.isocalendar().week == current_week)
            },
        )
    elif period_type == "M":
        current_period_df = filter_dataframe(
            df,
            {
                "Дата операции": lambda dates: (dates <= parsed_date)
                & (dates.dt.year == current_year)
                & (dates.dt.month == current_month)
            },
        )
    elif period_type == "Y":
        current_period_df = filter_dataframe(
            df,
            {"Дата операции": lambda dates: (dates <= parsed_date) & (dates.dt.year == current_year)},
        )
    else:
        current_period_df = filter_dataframe(
            df,
            {"Дата операции": lambda dates: (dates <= parsed_date)},
        )
    if "Номер карты" in current_period_df.columns:
        current_period_df["Номер карты"] = current_period_df["Номер карты"].astype(str).str[-4:]

    return current_period_df
