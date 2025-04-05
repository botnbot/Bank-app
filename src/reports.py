import json
import logging
import os
from logging import DEBUG, Formatter, getLogger
from typing import Any, Optional

import pandas as pd
from pandas import DataFrame, Timestamp

from config import ROOT_PATH
from src.decorators import save_to_file
from src.utils import filter_dataframe, get_3_months_data

# Настройка логирования
loger = getLogger("reports")
formatter = Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
loger.setLevel(DEBUG)

if not loger.handlers:
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
def get_report_by_category(df: DataFrame, category: str, date: Optional[Timestamp] = None) -> Any:
    """
        Функция возвращает траты по заданной категории за последние 3 месяца (от переданной даты).

    Args:
        df: DataFrame с транзакциями
        date: Дата, от которой рассчитывается период (формат 'DD.MM.YYYY')
        category (str): Название категории расходов для фильтрации

    Returns:
        Строка с JSON-данными
    """
    df = df.copy()
    three_month_transactions = get_3_months_data(df, date)
    loger.info(f"Транзакции за 3 месяца до {date} отфильтрованы")

    # Фильтруем транзакции по категории
    result_df = filter_dataframe(three_month_transactions, {"Категория": category})
    loger.info(f"Транзакции отфильтрованы по категории '{category}'")
    json_result = result_df.to_json(orient="records", force_ascii=False)

    return json.loads(json_result)


@save_to_file()
def expenses_by_days_of_the_week(df: pd.DataFrame, date: Optional[str] = None) -> list[dict]:
    """Возвращает средние траты по дням недели за последние 3 месяца от указанной даты.

    Args:
        df: DataFrame с транзакциями
        date: Дата, от которой рассчитывается период (формат 'DD.MM.YYYY')

    Returns:
        Список словарей с днями недели и средними тратами
    """
    WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    df = df.copy()
    three_month_transactions = get_3_months_data(df, date)
    if date is None or pd.to_datetime(date, errors="coerce") is pd.NaT:
        print("Дата не передана")
        return []
    loger.info(f"Транзакции за 3 месяца до {date} отфильтрованы")

    three_month_transactions["Дата операции"] = pd.to_datetime(
        three_month_transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce"
    )
    expenses = three_month_transactions[three_month_transactions["Сумма операции"] < 0].copy()
    if expenses.empty:
        loger.error("Нет транзакций с расходами!")
        raise ValueError("Нет данных о расходах за указанный период")

    expenses["День недели"] = pd.Categorical(
        expenses["Дата операции"].dt.day_name(), categories=WEEKDAY_ORDER, ordered=True
    )
    result = (
        expenses.groupby("День недели", observed=False)["Сумма операции"]
        .mean()
        .abs()
        .round(2)
        .reindex(WEEKDAY_ORDER)
        .reset_index()
        .rename(columns={"Сумма операции": "Средние траты"})
        .to_dict(orient="records")
    )

    loger.info("Успешно сгруппированы траты по дням недели")
    return result
