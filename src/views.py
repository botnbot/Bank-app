from datetime import datetime
from typing import Any, Union

import pandas as pd
from pandas import DataFrame, Series

from src.utils import filter_dataframe, get_data


def get_operations_for_current_month(df: DataFrame, current_date: Union[str, datetime] = datetime.now()) -> DataFrame:
    """
    Функция принимает DataFrame со всеми транзакциями и возвращает DataFrame с транзакциями за текущий месяц.
    Args:
        df (DataFrame): Исходный DataFrame с транзакциями.
        current_date (Union[str, datetime]): Текущая дата для определения текущего месяца.
    Returns:
        DataFrame: Отфильтрованный DataFrame с транзакциями за текущий месяц.
    """
    # Если текущая дата передана в виде строки, преобразуем её в datetime
    if isinstance(current_date, str):
        parsed_date = pd.to_datetime(current_date, format="%d.%m.%Y %H:%M:%S", errors="coerce")
        if pd.isnull(parsed_date):
            raise ValueError(f"Передана некорректная дата: {current_date}")
        current_date = parsed_date  # Преобразование успешно, обновляем current_date

    if not isinstance(current_date, datetime):
        raise ValueError(
            "Аргумент (current_date) должен быть строкой в формате 'дд.мм.гггг чч:мм:сс' или объектом datetime"
        )

    # Преобразуем столбец "Дата операции" в datetime
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce", dayfirst=True)

    # Извлекаем текущий месяц и год
    current_month = current_date.month
    current_year = current_date.year

    # Фильтруем DataFrame по текущему месяцу и году
    current_month_df = filter_dataframe(
        df,
        {"Дата операции": lambda dates: (dates.dt.month == current_month) & (dates.dt.year == current_year)},
    )
    return current_month_df


def sum_by_category(df: DataFrame) -> Series[float]:
    """Функция возвращает суммы расходов по категориям"""
    result = df.groupby("Категория", as_index=False, dropna=True)["Сумма операции"].sum()
    return result


def get_total_spending(df: DataFrame) -> Any:
    """Функция возвращает сумму всех трат"""
    result = df["Сумма операции с округлением"].sum()
    return result


def get_cashback_sum(df: DataFrame) -> Any:
    """Функция возвращает сумму кэшбека"""
    result = df["Кэшбэк"].sum()
    return result


def get_top_5(df: DataFrame) -> DataFrame:
    """Функция возвращает Топ-5 по сумме транзакций"""
    df_top_five = df.sort_values(by="Сумма операции с округлением", ascending=False, inplace=False)
    return df_top_five[["Дата операции", "Сумма операции с округлением", "Категория", "Описание"]].head(5)


if __name__ == "__main__":
    # Полный DataFrame
    df = get_data("data/operations.xlsx")

    # DataFrame со всеми операциями за текущий месяц (от переданной даты)
    df_current_month = get_operations_for_current_month(df, "09.04.2020 15:22:13")

    # DataFrame с тратами по категориям за текущий месяц (от переданной даты)
    spending_by_category = sum_by_category(df_current_month)

    # Сумма всех операций за текущий месяц
    total_spent = get_total_spending(df_current_month)
    print(f"Сумма всех операций за текущий месяц {total_spent}")

    # Кэшбек за текущий месяц
    cashback = get_cashback_sum(df_current_month)
    print(f"Кэшбек за текущий месяц {cashback}")

    # Топ-5 транзакций за текущий месяц
    top_five = get_top_5(df_current_month)
    print("Топ-5 транзакций за текущий месяц")
    print(top_five)
