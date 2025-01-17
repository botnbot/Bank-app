from datetime import datetime
from typing import Union

import pandas as pd
from pandas import DataFrame

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
            "Аргумент (current_date) должен быть строкой" f" в формате 'дд.мм.гггг чч:мм:сс' или объектом datetime"
        )

    # Преобразуем столбец "Дата операции" в datetime
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce")

    # Извлекаем текущий месяц и год
    current_month = current_date.month
    current_year = current_date.year

    # Фильтруем DataFrame по текущему месяцу и году
    current_month_df = filter_dataframe(
        df,
        {"Дата операции": lambda dates: (dates.dt.month == current_month) & (dates.dt.year == current_year)},
    )
    return current_month_df


if __name__ == "__main__":
    df = get_data("data/operations.xlsx")
    print(df.head())
    print(get_operations_for_current_month(df, "09.04.2020 15:22:13"))
