import logging
import os
from datetime import datetime
from logging import DEBUG, WARNING, Formatter, getLogger
from typing import Any, Union

import pandas as pd
from dateutil.relativedelta import relativedelta

from config import ROOT_PATH
from src.decorators import save_to_file
from src.utils import filter_dataframe, get_data, get_date


@save_to_file()
def get_report_by_category() -> Union[str, Any]:
    """Возвращает JSON с тратами по категории за последние 3 месяца."""

    loger = getLogger("reports")

    if not loger.handlers:  # Избегаем дублирования хендлеров
        formatter = Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        consolehandler = logging.StreamHandler()
        consolehandler.setFormatter(formatter)
        consolehandler.setLevel(DEBUG)

        logpath = os.path.join(ROOT_PATH, "logs")
        os.makedirs(logpath, exist_ok=True)
        logfile = os.path.join(logpath, "log.txt")

        try:
            filehandler = logging.FileHandler(logfile, mode="a")
            filehandler.setFormatter(formatter)
            filehandler.setLevel(WARNING)
            loger.addHandler(consolehandler)
            loger.addHandler(filehandler)
        except PermissionError as e:
            loger.error(f"Ошибка доступа к файлу логов: {e}")

    optional_date = get_date()
    if optional_date is None:
        date = datetime.now()
        loger.warning("Дата не передана, используется текущая дата")
    else:
        date = datetime.strptime(optional_date, "%Y-%m-%d %H:%M:%S")
        loger.debug(f"Дата передана: {date}")

    old_date = date - relativedelta(months=3)
    data_path = os.path.join(ROOT_PATH, "data", "operations.xlsx")

    df = get_data(data_path)
    loger.debug("Данные из файла получены")

    df["Дата операции временная"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")

    # Фильтрация по дате
    df = df[(df["Дата операции временная"] >= old_date) & (df["Дата операции временная"] <= date)]
    df = df.drop(columns=["Дата операции временная"])
    loger.debug(f'Данные отфильтрованы по дате:\n{df["Дата операции"]}')

    # Фильтрация по категории
    category = "Супермаркеты"
    filter_conditions = {"Категория": category}
    result = filter_dataframe(df, filter_conditions)
    loger.debug(f'Данные отфильтрованы по категории:\n{result["Категория"]}')

    return result.to_json(orient="records", force_ascii=False)


if __name__ == "__main__":
    getLogger("reports").setLevel(DEBUG)  # Логируем только в main
    get_report_by_category()
