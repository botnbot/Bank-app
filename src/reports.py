from datetime import datetime
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta
from pandas import DataFrame

from src.utils import filter_dataframe, get_data


def get_report_by_category(data_path: str, category: str, optional_date: Optional[str] = None) -> DataFrame:
    """Функция возвращает траты по заданной категории за последние 3 месяца (от переданной даты).
     Args:
        data_path (str): путь к исходному DataFrame.
        category (str): категория, по которой нужно отфильтровать DataFrame.
        optional_date (str): опциональная дата. Если дата не передана, то берется текущая дата.
    Returns:
        DataFrame: Отфильтрованный DataFrame."""
    if optional_date is None:
        date = datetime.now()
    else:
        date = datetime.strptime(optional_date, "%d.%m.%Y")
    old_date = date - relativedelta(months=3)
    df = get_data(data_path)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")
    df = df[(df["Дата операции"] >= old_date) & (df["Дата операции"] <= date)]
    filter_conditions = {"Категория": category}
    return filter_dataframe(df, filter_conditions)


if __name__ == "__main__":
    input_date = input('Введите дату в формате ДД.ММ.ГГГГ. В базе данные с 01.01.2018 по 31.12.2021')
    print(get_report_by_category("data/operations.xlsx", "Супермаркеты", input_date))
