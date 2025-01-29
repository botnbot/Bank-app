import os
from datetime import datetime
from typing import Optional, Any

import pandas as pd
from dateutil.relativedelta import relativedelta
from pandas import DataFrame

from config import ROOT_PATH
from src.decorators import save_to_file
from src.utils import filter_dataframe, get_data


@save_to_file()
def get_report_by_category(data_path: str, category: str, optional_date: Optional[str] = None) -> Any:
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
        date = datetime.strptime(optional_date, "%Y-%m-%d %H:%M:%S")
    old_date = date - relativedelta(months=3)
    df = get_data(data_path)
    df["Дата операции временная"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")

    # Фильтруем DataFrame по дате за последние 3 месяца
    df = df[(df["Дата операции временная"] >= old_date) & (df["Дата операции временная"] <= date)]
    df = df.drop(columns=["Дата операции временная"])

    # Фильтруем DataFrame по переданной категории
    filter_conditions = {"Категория": category}
    result = filter_dataframe(df, filter_conditions)

    return result.to_json(orient="records", force_ascii=False)


# if __name__ == "__main__":
#     while True:
#         try:
#             date: Optional[str] = input(
#                 "Введите строку с датой и временем в формате YYYY-MM-DD HH:MM:SS"
#                 " в диапазоне с 2018-01-01 по 2021-12-31,"
#                 " или нажмите Enter для использования текущей даты: "
#             ).strip()
#             if not date:  # Пустой ввод — текущая дата
#                 date = None
#             data_path = os.path.join(ROOT_PATH, 'data', 'operations.xlsx')
#             print(get_report_by_category(data_path, "Супермаркеты",date))
#             break
#         except ValueError as e:
#             print(e)
