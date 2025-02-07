import re
from datetime import datetime
from typing import Any, Optional

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


def get_df_for_current_period(date: str, df: DataFrame, period_type: str = "M") -> Any:
    """
    Фильтрует DataFrame по заданному периоду (неделя, месяц, год, все время).
    :param:
        date:str Дата в формате "YYYY-MM-DD HH:MM:SS"
        df:DataFrame Исходный DataFrame с транзакциями
        period_type:str необязательный параметр — диапазон данных. По умолчанию диапазон равен одному месяцу
                    (с начала месяца, на который выпадает дата, по саму дату).
                    Возможные значения этого необязательного параметра:
                    W — неделя, на которую приходится дата;
                    M — месяц, на который приходится дата;
                    Y — год, на который приходится дата;
                    ALL — все данные до указанной даты.
    :return:
        Отфильтрованный DataFrame
    """

    parsed_date = pd.to_datetime(date, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    if pd.isna(parsed_date):
        raise ValueError("Ошибка: передана некорректная дата!")
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
    return current_period_df
