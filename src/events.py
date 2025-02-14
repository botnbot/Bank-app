import json
import logging
import os
from logging import DEBUG, Formatter, getLogger

import pandas as pd

from config import ROOT_PATH
from src.external_api import convert_to_rub, get_exchange_rates, get_stock_prices
from src.utils import get_data, get_df_for_current_period

loger = getLogger("events")
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
    filehandler.setLevel(logging.WARNING)
    filehandler.setFormatter(formatter)
    if not loger.handlers:
        loger.addHandler(consolehandler)
        loger.addHandler(filehandler)
except PermissionError as e:
    loger.error(f"Ошибка доступа к файлу логов: {e}")


def events(
        date: str,
        period_type: str = "M"
) -> str:
    """Главная функция для страницы events.
    Args:
        date (str): строка с датой
        range(str): Диапазон данных. По умолчанию диапазон равен одному месяцу
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

    loger.info("Получение данных для страницы 'События'")
    # Загрузка пользовательских настроек
    user_settings_path = os.path.join(ROOT_PATH, "user_settings.json")
    with open(user_settings_path, "r") as f:
        user_settings = json.load(f)
    stocks = user_settings["user_stocks"]
    currency = user_settings["user_currencies"]
    loger.info("Пользовательские настройки получены")

    # Загрузка данных
    data_path = os.path.join(ROOT_PATH, "data", "operations.xlsx")
    df = get_data(data_path)
    loger.info("Транзакции из файла загружены")

    df = get_df_for_current_period(date, df, period_type)
    loger.info("Данные за период отфильтрованы")

    # Преобразуем столбец "Дата операции" в datetime
    df = df.copy()  # Создаём копию, чтобы избежать SettingWithCopyWarning
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce", dayfirst=True)

    # Расходы
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
        transfers_and_cash["amount"].round().apply(lambda x: f"{x:g}")
    )  # Округление и отбрасывание ,0
    loger.info("Данные проанализированы")

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
    rates = get_exchange_rates(currency)
    loger.info("Запрос курса валют")
    rub_rates = convert_to_rub(rates)
    currency_rates_formatted = [{"currency": cur, "rate": rate} for cur, rate in rub_rates.items()]
    loger.info("Получены курсы валют")
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
    loger.info("Данные сформированы")
    return json.dumps(result, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    print(events("2018-05-10 22:22:22", "ALL"))
