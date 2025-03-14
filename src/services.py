import locale
import logging
import os.path
import re
from logging import DEBUG, Formatter, getLogger
from typing import Any, Dict, List

import pandas as pd

from config import ROOT_PATH
from src.decorators import save_to_file
from src.utils import filter_dataframe, get_data

loger = getLogger("services")
formatter = Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
loger.setLevel(DEBUG)
locale.setlocale(locale.LC_TIME, "Russian_Russia.1251")

consolehandler = logging.StreamHandler()
consolehandler.setFormatter(formatter)
consolehandler.setLevel(DEBUG)

logpath = os.path.join(ROOT_PATH, "logs")
os.makedirs(logpath, exist_ok=True)
logfile = os.path.join(ROOT_PATH, "logs", "log.txt")

try:
    filehandler = logging.FileHandler(logfile, mode="a")
    filehandler.setFormatter(formatter)
    filehandler.setLevel(logging.WARNING)
    if not loger.handlers:
        loger.addHandler(consolehandler)
        loger.addHandler(filehandler)
except PermissionError as e:
    loger.error(f"Ошибка доступа к файлу логов: {e}")


@save_to_file()
def find_money_transfers_from_individuals(data_path: str) -> Any:
    """
    Функция, возвращающая JSON с переводами только физическим лицам.
     Args:
        data_path (str): путь к исходному DataFrame.
    Returns:
        str: Отфильтрованный JSON
    """

    try:
        full_data_path = os.path.join(ROOT_PATH, data_path)
        df = get_data(full_data_path)
        loger.info("Данные из файла загружены")
    except FileNotFoundError as e:
        loger.error(f"Ошибка доступа к файлу с данными: {e}")
        raise FileNotFoundError("Файл с данными не найден")

    pattern = re.compile(r"^\s*[A-ZА-ЯЁ]{1}[a-zа-яё]+\s+[A-ZА-ЯЁ]{1}\.\s*$")
    filter_conditions = {"Категория": "Переводы", "Описание": pattern}
    result = filter_dataframe(df, filter_conditions, "AND")
    loger.info("Ответ сформирован")
    return result.to_json(orient="records", force_ascii=False)


@save_to_file()
def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """
    Рассчитывает сумму, которую можно отложить в «Инвесткопилку» за заданный месяц.

    Args:
        month (str): Месяц, для которого рассчитывается сумма (формат 'YYYY-MM').
        transactions (List[Dict[str, Any]]): Список транзакций, каждая из которых содержит:
            - "Дата операции" (str): Дата транзакции (формат 'YYYY-MM-DD').
            - "Сумма операции" (float): Сумма операции в оригинальной валюте.
        limit (int): Предел округления сумм операций.

    Returns:
        float: Сумма, которую можно отложить в «Инвесткопилку».
    """
    savings = 0

    # Преобразуем месяц в datetime для фильтрации
    parsed_month = pd.to_datetime(month, format="%Y-%m", errors="coerce", yearfirst=True)
    if pd.isna(parsed_month):
        raise ValueError("Ошибка: передана некорректная дата! Запустите с корректными параметрами.")
    loger.info(f"Используются данные за {parsed_month.strftime("%B")} {parsed_month.year}")

    # Фильтруем транзакции по месяцу
    for transaction in transactions:
        transaction_date = pd.to_datetime(transaction["Дата операции"], errors="coerce", dayfirst=True)
        if pd.isna(transaction_date):
            loger.warning(f"Пропущена некорректная дата {transaction_date}")
            continue  # Пропускаем некорректные даты

        if transaction_date.year == parsed_month.year and transaction_date.month == parsed_month.month:
            remainder = transaction["Сумма операции"] % limit
            if remainder != 0:
                savings += limit - remainder
    return round(savings, 2)
