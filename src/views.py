import json
import logging
import os
from datetime import datetime
from logging import Formatter, DEBUG, getLogger, WARNING
from typing import Any, Optional, Union

import pandas as pd
from pandas import DataFrame

from config import ROOT_PATH
from src.decorators import save_to_file
from src.external_api import convert_to_rub, get_exchange_rates, get_stock_prices
from src.utils import filter_dataframe, get_data, greetings


def get_operations_for_current_month(df: DataFrame, current_date: Union[str, datetime, Any, None] = None) -> Any:
    """
    Функция принимает DataFrame со всеми транзакциями и возвращает DataFrame с транзакциями за текущий месяц.
    Args:
        df (DataFrame): Исходный DataFrame с транзакциями.
        current_date (Union[str, datetime, None]): Текущая дата для определения текущего месяца.
    Returns:
        DataFrame: Отфильтрованный DataFrame с транзакциями за текущий месяц.
    """
    # Если current_date не передана, используем текущую дату
    if current_date is None:
        current_date_dt = datetime.now()
    elif isinstance(current_date, str):
        # Преобразование строки в datetime
        parsed_date = pd.to_datetime(current_date, format="%Y-%m-%d %H:%M:%S", errors="coerce")
        if pd.isnull(parsed_date):
            raise ValueError(f"Передана некорректная дата: {current_date}")
        current_date_dt = parsed_date  # Преобразование успешно
    elif isinstance(current_date, datetime):
        current_date_dt = current_date
    else:
        raise ValueError(
            "Аргумент (current_date) должен быть строкой в формате 'YYYY-MM-DD HH:MM:SS', объектом datetime или None"
        )

    # Преобразуем столбец "Дата операции" в datetime
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce", dayfirst=True)

    # Извлекаем текущий месяц и год
    current_month = current_date_dt.month
    current_year = current_date_dt.year
    # Фильтруем DataFrame по текущему месяцу и году
    current_month_df = filter_dataframe(
        df,
        {
            "Дата операции": lambda dates: (dates <= current_date_dt)
            & (dates.dt.year == current_year)
            & (dates.dt.month == current_month)
        },
    )
    return current_month_df


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
        Series: Series с суммами всех транзакций и суммами кэшбека по каждой карте."""
    result = df.groupby("Номер карты", as_index=False, dropna=True)[["Сумма операции с округлением", "Кэшбэк"]].sum()
    return result


def get_top_5(df: DataFrame) -> DataFrame:
    """Функция возвращает Топ-5 по сумме транзакций"""
    df_top_five = df.sort_values(by="Сумма операции с округлением", ascending=False, inplace=False)
    return df_top_five[["Дата операции", "Сумма операции с округлением", "Категория", "Описание"]].head(5)

@save_to_file()
def main() -> str:
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
    loger = getLogger('views')
    loger.setLevel(DEBUG)

    formatter = Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    consolehandler = logging.StreamHandler()
    consolehandler.setFormatter(formatter)
    consolehandler.setLevel(DEBUG)

    logpath = os.path.join(ROOT_PATH, 'logs')
    os.makedirs(logpath, exist_ok=True)  # Создаём только папку, а не файл!
    logfile = os.path.join(ROOT_PATH, 'logs', 'log.txt')
    try:
        filehandler = logging.FileHandler(logfile, mode="a")
        filehandler.setLevel(WARNING)
        filehandler.setFormatter(formatter)
        if not loger.handlers:
            loger.addHandler(consolehandler)
            loger.addHandler(filehandler)
    except PermissionError as e:
        loger.error(f"Ошибка доступа к файлу логов: {e}")

    loger.info("Запуск")
    # Загрузка данных
    data_path = os.path.join(ROOT_PATH, "data", "operations.xlsx")
    df = get_data(data_path)
    loger.info("Данные из файла загружены")

    # Получение даты
    date = get_date()

    # Получение операций за текущий месяц
    df_current_month = get_operations_for_current_month(df, date)
    loger.info("данные за текущий месяц получены")
    # Общая сумма операций и кэшбэк по картам
    total_spent_df = get_total_spending(df_current_month)
    total_spent_df["last_digits"] = total_spent_df["Номер карты"].astype(str).str[-4:]
    cards = total_spent_df.rename(columns={"Сумма операции с округлением": "total_spent", "Кэшбэк": "cashback"})[
        ["last_digits", "total_spent", "cashback"]
    ].to_dict(orient="records")
    loger.info("Данные по картам обработаны")

    # Топ-5 транзакций
    top_five = get_top_5(df_current_month)
    top_five["Дата операции"] = top_five["Дата операции"].dt.strftime("%d.%m.%Y")  # Преобразование формата даты
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
            if "Ошибка API" in price:
                loger.warning(f"Ошибка API. Не удалось получить курс акций для {stock}")
            else:
                stock_prices_formatted.append({"stock": stock, "price": price})
    except Exception as e:
        loger.error(f"Ошибка API при получении курсов акций: {e}")
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


    # Финальный JSON-ответ
    result = {
        "greeting": greetings(),
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates_formatted,
        "stock_prices": stock_prices_formatted,
    }
    loger.info("Ответ сформирован")
    return json.dumps(result, indent=4, ensure_ascii=False)



def get_date() -> Optional[str]:
    while True:
        try:
            date: Optional[str] = input(
                "Введите строку с датой и временем в формате YYYY-MM-DD HH:MM:SS"
                " в диапазоне с 2018-01-01 по 2021-12-31,"
                " или нажмите Enter для использования текущей даты: "
            ).strip()
            if not date:
                date = None
            break
        except ValueError as e:
            raise ValueError('Неверный формат даты')
    return date


if __name__ == "__main__":
    print(main())