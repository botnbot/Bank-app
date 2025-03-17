import logging
import os
from datetime import datetime
from logging import DEBUG, Formatter, getLogger
from typing import Any, Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

from config import ROOT_PATH
from src.decorators import save_to_file
from src.utils import filter_dataframe, get_data

# Настройка логирования
loger = getLogger("reports")
formatter = Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
loger.setLevel(DEBUG)

if not loger.handlers:  # Добавляем обработчики только если их еще нет
    consolehandler = logging.StreamHandler()
    consolehandler.setFormatter(formatter)
    consolehandler.setLevel(DEBUG)

    logpath = os.path.join(ROOT_PATH, "logs")
    os.makedirs(logpath, exist_ok=True)
    logfile = os.path.join(logpath, "log.txt")

    try:
        filehandler = logging.FileHandler(logfile, mode="a")
        filehandler.setFormatter(formatter)
        filehandler.setLevel(logging.WARNING)

        loger.addHandler(consolehandler)
        loger.addHandler(filehandler)
    except PermissionError as e:
        loger.error(f"Ошибка доступа к файлу логов: {e}")


@save_to_file()
def get_report_by_category(data_path: str, category: str, optional_date: Optional[str] = None) -> Any:
    """Функция возвращает траты по заданной категории за последние 3 месяца (от переданной даты).
     Args:
        data_path (str): путь к исходному DataFrame.
        category (str): категория, по которой нужно отфильтровать DataFrame.
        optional_date (str): опциональная дата. Если дата не передана, то берется текущая дата.
    Returns:
        DataFrame: Отфильтрованный DataFrame."""
    date = None
    if optional_date is None:
        date = datetime.now()
    else:
        try:
            date = datetime.strptime(optional_date, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            loger.error(f"Ошибка при разборе даты: {e}")
            raise ValueError("Некорректный формат даты, используйте 'YYYY-MM-DD HH:MM:SS'")

    old_date = date - relativedelta(months=3)

    try:
        full_data_path = os.path.join(ROOT_PATH, data_path)
        df = get_data(full_data_path)
        loger.info(f"Данные из файла {full_data_path} загружены")
    except FileNotFoundError as e:
        loger.error(f"Ошибка доступа к файлу с данными: {e}")
        raise FileNotFoundError("Файл с данными не найден")

    # Фильтруем DataFrame по дате за последние 3 месяца

    df["Дата операции временная"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["Дата операции временная"])
    df = df[(df["Дата операции временная"] >= old_date) & (df["Дата операции временная"] <= date)]
    df = filter_dataframe(df, {"Категория": category})
    loger.info(f"Данные отфильтрованы по дате с {old_date} по {date}")
    df = df.drop(columns=["Дата операции временная"])

    loger.info(f"Данные отфильтрованы по категории '{category}'")
    filter_conditions = {"Категория": category}
    result = filter_dataframe(df, filter_conditions)
    loger.info("Данные сформированы")
    return result.to_json(orient="records", force_ascii=False)
