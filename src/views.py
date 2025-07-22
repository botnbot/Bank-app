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


if not getattr(loger, "LOG_INITIALIZED", False):  # Проверяем наличие атрибута
    setattr(loger, "LOG_INITIALIZED", True)  # Устанавливаем атрибут

    consolehandler = logging.StreamHandler()
    consolehandler.setFormatter(formatter)
    consolehandler.setLevel(DEBUG)
    loger.addHandler(consolehandler)

    logpath = os.path.join(ROOT_PATH, "logs")
    os.makedirs(logpath, exist_ok=True)
    logfile = os.path.join(logpath, "log.txt")

    try:
        filehandler = logging.FileHandler(logfile, mode="a")
        filehandler.setLevel(WARNING)
        filehandler.setFormatter(formatter)
        loger.addHandler(filehandler)
    except PermissionError:
        loger.error("Ошибка доступа к файлу логов")


def sum_by_category(df: DataFrame) -> DataFrame:
    """
    Функция возвращает суммы расходов по категориям
    Args:
        df (DataFrame): Исходный DataFrame с транзакциями.
    Returns:
        DataFrame с суммами транзакций по каждой категории.
    """

    result: DataFrame = (
        df.groupby("Категория", dropna=True)["Сумма операции"]
        .sum()
        .reset_index()
        .query("`Сумма операции` < 0")  # оставляем только расходы
    )
    result["Сумма операции"] = result["Сумма операции"].abs()  # делаем суммы положительными

    return result


def get_total_spend(df: DataFrame) -> Any:
    """
    Функция осуществляет группировку сумм всех трат по каждой карте
    Args:
        df (DataFrame): Исходный DataFrame с транзакциями.
    Returns:
        DataFrame (DataFrame): DataFrame с суммами всех транзакций и суммами кэшбека по каждой карте.
    """

    if df.empty or not {"Номер карты", "Сумма операции с округлением", "Кэшбэк"}.issubset(df.columns):
        return pd.DataFrame(columns=["Номер карты", "Сумма операции с округлением", "Кэшбэк"])
    return df.groupby("Номер карты", as_index=False, dropna=True)[["Сумма операции с округлением", "Кэшбэк"]].sum()


def get_top_5(df: DataFrame) -> DataFrame:
    """
    Функция возвращает Топ-5 по сумме платежа
    Args:
        df: исходный DataFrame с транзакциями
    Returns:
        отфильтрованный DataFrame, содержащий топ-5 транзакций
    """
    df_top_five = df.sort_values(by="Сумма операции", ascending=False, inplace=False)

    return df_top_five[["Дата операции", "Сумма операции", "Категория", "Описание"]].head(5)


@save_to_file()
def views(date: str) -> str:
    """
    Функция формирует данные для страницы ***Главная***
    Args:
        date : строка с датой и временем в формате YYYY-MM-DD HH:MM:SS
    Returns:
        str : JSON-строка, содержащая следующие данные:
         Приветствие в формате "???", где ??? — «Доброе утро» / «Добрый день» / «Добрый вечер» / «Доброй ночи»
         в зависимости от текущего времени.
         По каждой карте:
             последние 4 цифры карты, общая сумма расходов, кешбэк (1 рубль на каждые 100 рублей).
             Топ-5 транзакции по сумме платежа.
         Курс валют.
         Стоимость акций из S&P 500.
    """

    # Загрузка данных
    data_path = os.path.join(ROOT_PATH, "data/operations.xlsx")
    df = get_data(data_path)
    loger.info(f"Транзакции из файла {data_path} загружены")

    # Получение операций за текущий месяц
    df_current_month = get_df_for_current_period(date, df)
    df_current_month = df_current_month[
        df_current_month["Номер карты"].apply(lambda x: pd.notna(x) and str(x).strip() != "")
    ]
    loger.info("Удалены транзакции с отсутствующим номером карты")
    loger.info(f"Транзакции за {date[:-12]} отфильтрованы")
    # Общая сумма операций и кэшбэк по картам
    total_spent_df = get_total_spend(df_current_month)

    # Преобразуем список словарей в DataFrame
    if isinstance(total_spent_df, list):
        total_spent_df = pd.DataFrame(total_spent_df)

    def extract_last_digits(card_number):
        if pd.isna(card_number):
            return "неизвестно"
        card_str = str(card_number).strip()
        if card_str.isdigit() and len(card_str) >= 4:
            return card_str[-4:]
        return "неизвестно"

    total_spent_df["last_digits"] = total_spent_df["Номер карты"].apply(extract_last_digits)

    cards = total_spent_df.rename(columns={'Сумма операции с округлением': "total_spent", "Кэшбэк": "cashback"})[
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
            "Сумма операции": "amount",
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
    loger.info("Пользовательские настройки  акций и валют получены")

    # Получение курсов акций
    stock_prices_formatted = []
    loger.info("Запрос курса акций.")
    try:
        stock_prices = get_stock_prices(stocks)
        for stock, price in stock_prices.items():
            if isinstance(price, str) and "Ошибка API" in price:
                loger.warning(f"Ошибка {stock}: {price}")
                stock_prices_formatted.append({"stock": stock, "price": price})
            elif isinstance(price, (int, float)):
                stock_prices_formatted.append({"stock": stock, "price": price})
            else:
                loger.warning(f"N/A {stock}: {price}")
                stock_prices_formatted.append({"stock": stock, "price": "N/A"})
    except Exception as e:
        loger.error(f"Неизвестная ошибка при получении курсов акций: {repr(e)}")
        stock_prices_formatted = [{"stock": stock, "price": f"Ошибка: {repr(e)}"} for stock in stocks]

    # Получение курсов валют
    loger.info("Запрос курса валют")
    currency_rates_formatted = []
    try:
        rates = get_exchange_rates(currency)
        rub_rates = convert_to_rub(rates)

        # Фильтрация корректных валют и логирование некорректных значений
        for cur, rate in rub_rates.items():
            if isinstance(cur, str) and cur.isalpha():
                currency_rates_formatted.append({"currency": cur, "rate": rate})
            else:
                loger.warning(f"Пропущен некорректный код валюты: {cur}")
    except Exception as e:
        loger.warning(f"Ошибка при получении курсов валют: {e}")
        currency_rates_formatted = [
            {"currency": cur, "rate": f"{str(e)}"} for cur in currency if isinstance(cur, str) and cur.isalpha()
        ]

    result = {
        "greeting": greetings(),
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates_formatted,
        "stock_prices": stock_prices_formatted,
    }
    loger.info("Данные  для страницы 'Главная' сформированы")
    return json.dumps(result, indent=4, ensure_ascii=False)


@save_to_file()
def events(date: str, period_type: str = "M") -> str:
    """Главная функция для страницы events.
    Args:
        date (str): строка с датой
        period_type(str): Диапазон данных. По умолчанию диапазон равен одному месяцу
                    (с начала месяца, на который выпадает дата, по саму дату).
                    Возможные значения этого параметра:
                    W — неделя, на которую приходится дата;
                    M — месяц, на который приходится дата;
                    Y — год, на который приходится дата;
                    ALL — все данные до указанной даты.
    Returns:
        str: Возвращаемый JSON-ответ содержит следующие данные:
        «Расходы»: Общая сумма расходов.
            Раздел «Основные расходы», в котором траты по категориям отсортированы по убыванию.
                Данные предоставляются по 7 категориям с наибольшими тратами, траты по остальным категориям
                суммируются и попадают в категорию «Остальное».
            Раздел «Переводы и наличные», в котором сумма по категориям «Наличные» и «Переводы» отсортирована
             по убыванию.
        «Поступления»: Общая сумма поступлений.
            Раздел «Основные поступления», в котором поступления по категориям отсортированы по убыванию.
        Курс валют.
        Стоимость акций из S&P 500."""

    # Загрузка пользовательских настроек
    user_settings_path = os.path.join(ROOT_PATH, "user_settings.json")
    with open(user_settings_path, "r") as f:
        user_settings = json.load(f)
    stocks = user_settings["user_stocks"]
    currency = user_settings["user_currencies"]
    loger.info("Пользовательские настройки получены")

    # Загрузка данных
    data_path = os.path.join(ROOT_PATH, "data/operations.xlsx")
    full_df = get_data(data_path)
    loger.info(f"Транзакции из файла {data_path} загружены")
    df = get_df_for_current_period(date, full_df, period_type)
    loger.info("Данные за период отфильтрованы")
    df = df.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce", dayfirst=True)

    # Транзакции с расходами
    expenses = df[df["Сумма платежа"] < 0]
    # Общая сумма расходов
    total_expenses = round((expenses["Сумма платежа"]).sum())
    # Группировка по категориям расходов
    category_expenses = expenses.groupby("Категория", as_index=False, dropna=True)[["Сумма платежа"]].sum()
    # Сортировка групп по сумме расходов
    sorted_category_expenses = category_expenses.sort_values(by="Сумма платежа", key=abs, ascending=False)

    # Переводы и наличные
    transfers_and_cash_df = expenses[(expenses["Категория"] == "Наличные") | (expenses["Категория"] == "Переводы")]
    category_transfers_and_cash = transfers_and_cash_df.groupby("Категория", as_index=False, dropna=True)[
        ["Сумма платежа"]
    ].sum()
    sorted_category_transfers_and_cash = category_transfers_and_cash.sort_values(
        by="Сумма платежа", key=abs, ascending=False
    )

    # Семь категорий с наибольшими тратами
    top_seven = sorted_category_expenses.head(7)
    # Сумма семи категорий с наибольшими тратами
    main_expenses = sorted_category_expenses.head(7)["Сумма платежа"].sum()
    # Сумма остальных трат
    other = round(total_expenses - main_expenses)
    other_row = pd.DataFrame({"Категория": ["Остальное"], "Сумма платежа": [other]})
    top_seven = pd.concat([top_seven, other_row], ignore_index=True)

    # Поступления
    income = df[df["Сумма платежа"] > 0]
    # Сумма поступлений
    total_income = round(income["Сумма платежа"].sum())
    # Группировка по категориям поступлений
    category_incomme = income.groupby("Категория", as_index=False, dropna=True)[["Сумма платежа"]].sum()
    # Отсортированные группы поступлений
    sorted_category_income = category_incomme.sort_values(by="Сумма платежа", ascending=False)

    top_expenses = top_seven.rename(columns={"Сумма платежа": "amount", "Категория": "category"})
    top_expenses["amount"] = top_expenses["amount"].round().apply(lambda x: f"{x:g}")  # Округление и отбрасывание ,0
    top_income = sorted_category_income.rename(columns={"Сумма платежа": "amount", "Категория": "category"})
    top_income["amount"] = top_income["amount"].round().apply(lambda x: f"{x:g}")  # Округление и отбрасывание ,0
    transfers_and_cash = sorted_category_transfers_and_cash.rename(
        columns={"Сумма платежа": "amount", "Категория": "category"}
    )
    transfers_and_cash["amount"] = (
        transfers_and_cash["amount"].round().apply(lambda x: f"{x:g}")  # Округление и отбрасывание ,0
    )
    loger.info("Данные проанализированы")

    # Получение курсов акций
    stock_prices_formatted = []
    loger.info("Запрос курса акций.")
    try:
        stock_prices = get_stock_prices(stocks)
        for stock, price in stock_prices.items():
            if isinstance(price, str) and "Ошибка API" in price:
                loger.warning(f"Ошибка {stock}: {price}")
                stock_prices_formatted.append({"stock": stock, "price": price})
            elif isinstance(price, (int, float)):
                stock_prices_formatted.append({"stock": stock, "price": price})
            else:
                loger.warning(f"N/A {stock}: {price}")
                stock_prices_formatted.append({"stock": stock, "price": "N/A"})
    except Exception as e:
        loger.error(f"Неизвестная ошибка при получении курсов акций: {repr(e)}")
        stock_prices_formatted = [{"stock": stock, "price": f"Ошибка: {repr(e)}"} for stock in stocks]

    # Получение курсов валют
    loger.info("Запрос курса валют")
    currency_rates_formatted = []
    try:
        rates = get_exchange_rates(currency)
        rub_rates = convert_to_rub(rates)

        # Фильтрация корректных валют и логирование некорректных значений
        for cur, rate in rub_rates.items():
            if isinstance(cur, str) and cur.isalpha():
                currency_rates_formatted.append({"currency": cur, "rate": rate})
            else:
                loger.warning(f"Пропущен некорректный код валюты: {cur}")
    except Exception as e:
        loger.warning(f"Ошибка при получении курсов валют: {e}")
        currency_rates_formatted = [
            {"currency": cur, "rate": f"{str(e)}"} for cur in currency if isinstance(cur, str) and cur.isalpha()
        ]

    result = {
        "expenses": {
            "total_amount": total_expenses,
            "main": top_expenses.to_dict(orient="records"),
            "transfers_and_cash": transfers_and_cash.to_dict(orient="records"),
        },
        "income": {"total_amount": total_income, "main": top_income.to_dict(orient="records")},
        "currency_rates": currency_rates_formatted,
        "stock_prices": stock_prices_formatted,
    }
    loger.info("Данные  для страницы 'События' сформированы")
    return json.dumps(result, indent=4, ensure_ascii=False)
