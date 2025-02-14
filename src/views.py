import json
import logging
import os
from logging import DEBUG, WARNING, Formatter, getLogger
from typing import Any

import pandas as pd
from pandas import DataFrame

from config import ROOT_PATH
from src.decorators import save_to_file
from src.external_api import convert_to_rub, get_exchange_rates, get_stock_prices
from src.utils import get_data, get_df_for_current_period, greetings

loger = getLogger("views")
loger.setLevel(DEBUG)

formatter = Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

consolehandler = logging.StreamHandler()
consolehandler.setFormatter(formatter)
consolehandler.setLevel(DEBUG)

logpath = os.path.join(ROOT_PATH, "logs")
os.makedirs(logpath, exist_ok=True)
logfile = os.path.join(ROOT_PATH, "logs", "log.txt")
try:
    filehandler = logging.FileHandler(logfile, mode="a")
    filehandler.setLevel(WARNING)
    filehandler.setFormatter(formatter)
    if not loger.handlers:
        loger.addHandler(consolehandler)
        loger.addHandler(filehandler)
except PermissionError as e:
    loger.error(f"Ошибка доступа к файлу логов: {e}")


def sum_by_category(df: DataFrame) -> DataFrame:
    """
    Функция возвращает суммы расходов по категориям
    Args:
        df (DataFrame): Исходный DataFrame с транзакциями.
    Returns:
        DataFrame с суммами транзакций по каждой категории.
    """

    result: DataFrame = (
        df.groupby("Категория", dropna=True)["Сумма операции с округлением"]
        .sum()
        .reset_index()  # Преобразуем Series в DataFrame
    )
    return result


def get_total_spending(df: DataFrame) -> Any:
    """
    Функция возвращает сумму всех трат по каждой карте
    Args:
        df (DataFrame): Исходный DataFrame с транзакциями.
    Returns:
        DataFrame (DataFrame): DataFrame с суммами всех транзакций и суммами кэшбека по каждой карте."""
    result = df.groupby("Номер карты", as_index=False, dropna=True)[["Сумма операции с округлением", "Кэшбэк"]].sum()
    return result


def get_top_5(df: DataFrame) -> DataFrame:
    """
    Функция возвращает Топ-5 по сумме транзакции
    """
    df_top_five = df.sort_values(by="Сумма операции с округлением", ascending=False, inplace=False)

    return df_top_five[["Дата операции", "Сумма операции с округлением", "Категория", "Описание"]].head(5)


@save_to_file()
def views(date: str) -> str:
    """
    Функция, принимающая на вход строку с датой и временем в формате YYYY-MM-DD HH:MM:SS
     и возвращающую JSON-ответ со следующими данными:
     Приветствие в формате "???", где ??? — «Доброе утро» / «Добрый день» / «Добрый вечер» / «Доброй ночи»
      в зависимости от текущего времени.
      По каждой карте:
      последние 4 цифры карты, общая сумма расходов, кешбэк (1 рубль на каждые 100 рублей).
      Топ-5 транзакции по сумме платежа.
      Курс валют.
      Стоимость акций из S&P 500.
    """

    loger.info("Запуск")
    # Загрузка данных
    data_path = os.path.join(ROOT_PATH, "data", "operations.xlsx")
    df = get_data(data_path)
    loger.info("Транзакции из файла загружены")

    # Получение операций за текущий месяц
    df_current_month = get_df_for_current_period(date, df)
    loger.info(f"Транзакции за текущий месяц получены {date[:-12]}")
    # Общая сумма операций и кэшбэк по картам
    total_spent_df = get_total_spending(df_current_month)

    # Преобразуем список словарей в DataFrame
    if isinstance(total_spent_df, list):
        total_spent_df = pd.DataFrame(total_spent_df)

    total_spent_df["last_digits"] = total_spent_df["Номер карты"].astype(str).str[-4:]
    cards = total_spent_df.rename(columns={"Сумма операции с округлением": "total_spent", "Кэшбэк": "cashback"})[
        ["last_digits", "total_spent", "cashback"]
    ].to_dict(orient="records")
    loger.info("Данные по картам обработаны")

    # Топ-5 транзакций
    top_five = get_top_5(df_current_month)

    # Преобразуем в DataFrame, если возвращен список
    if isinstance(top_five, list):
        top_five = pd.DataFrame(top_five)

    # Преобразуем колонку в datetime
    top_five["Дата операции"] = pd.to_datetime(top_five["Дата операции"], errors="coerce")

    # Форматируем дату
    top_five["Дата операции"] = top_five["Дата операции"].dt.strftime("%d.%m.%Y")

    top_transactions = top_five.rename(
        columns={
            "Дата операции": "date",
            "Сумма операции с округлением": "amount",
            "Категория": "category",
            "Описание": "description",
        }
    ).to_dict(orient="records")
    loger.info("Топ-5 транзакций обработаны")

    # Загрузка пользовательских настроек
    user_settings_path = os.path.join(ROOT_PATH, "user_settings.json")
    with open(user_settings_path, "r") as f:
        user_settings = json.load(f)
    stocks = user_settings["user_stocks"]
    currency = user_settings["user_currencies"]
    loger.info("Пользовательские настройки получены")

    # Получение курсов акций
    try:
        stock_prices = get_stock_prices(stocks)
        loger.info("Запрос курса акций")

        stock_prices_formatted = []
        for stock, price in stock_prices.items():
            if isinstance(price, str) and "Ошибка API" in price:
                loger.warning(f"Ошибка API при получении курса акций для {stock}: {price}")
            else:
                stock_prices_formatted.append({"stock": stock, "price": price})

    except Exception as e:
        loger.error(f"Неизвестная ошибка при получении курсов акций: {repr(e)}")
        stock_prices_formatted = []

    # Получение курсов валют
    try:
        rates = get_exchange_rates(currency)
        loger.info("Запрос курса валют")
        rub_rates = convert_to_rub(rates)
        currency_rates_formatted = [{"currency": cur, "rate": rate} for cur, rate in rub_rates.items()]
        loger.info("Получен курс валют")
    except Exception as e:
        currency_rates_formatted = []
        loger.warning(f"Ошибка получения курсов валют: {e}")

    result = {
        "greeting": greetings(),
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates_formatted,
        "stock_prices": stock_prices_formatted,
    }
    loger.info("Ответ сформирован")
    return json.dumps(result, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    print(views("2021-02-09 17:05:48"))
