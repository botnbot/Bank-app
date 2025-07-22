import os

import finnhub  # type: ignore
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("apikey")


def get_stock_prices(symbols: tuple) -> dict:
    """
    Функция принимает кортеж с кодами акций и возвращает словарь, где ключи - тикеры, а значения это их цены.
    Args:
        symbols: tuple кортеж кодов акций
    Returns:
        dict: словарь, где ключи - тикеры, а значения это их цены.
    """
    finnhub_client = finnhub.Client(api_key=api_key)
    prices = {}
    for symbol in symbols:
        try:
            quote = finnhub_client.quote(symbol)
            if not quote or "c" not in quote or quote["c"] == 0:
                prices[symbol] = "N/A"
                continue
            prices[symbol] = quote["c"]
        except finnhub.exceptions.FinnhubAPIException as e:
            error_message = e.response.json() if hasattr(e.response, "json") else str(e)
            prices[symbol] = f"Ошибка {error_message}"
        except ValueError as e:
            prices[symbol] = f"Ошибка API {e}"
        except Exception as e:
            prices[symbol] = str(e)
    return prices


def get_exchange_rates(currency_codes: tuple = ("RUB",)) -> dict:
    """
    Функция принимает кортеж с кодами валют и возвращает словарь, где ключи это коды валют, а значения - это курсы
    этих валют
    Args:
        currency_codes: tuple кортеж с кодами валют
    Returns:
        dict словарь с кодами и курсами соответствующих валют
    """

    access_key = os.getenv("API_KEY")
    if not access_key:
        raise ValueError("API-ключ не найден. Убедитесь, что в переменную окружения задан действующий ключ")

    url = f"https://data.fixer.io/api/latest?access_key={access_key}"
    if "RUB" not in currency_codes:
        currency_codes += ("RUB",)
    querystring = {"base": "EUR", "symbols": ",".join(currency_codes)}
    response = requests.get(url, params=querystring)
    data = response.json()
    if not data.get("success"):
        error_info = data.get("error", {}).get("info", "Неизвестная ошибка.")
        raise ValueError(f"Ошибка API: {error_info}")

    rates = data.get("rates", {})
    return {code: rates.get(code, "N/A") for code in currency_codes}


def convert_to_rub(rates: dict, base_currency: str = "RUB") -> dict:
    """
    Пересчитывает курсы валют в значения относительно любой валюты.
    Принимает на вход словарь с курсами валют и код валюты, на которую надо произвести пересчет курсов.
    Возвращает словарь, где ключ — это код валюты, а значение — это курс этой валюты.
    Args:
        rates: dict словарь с курсами валют
        base_currency: str код базовой валюты, на которую надо произвести перерасчет (должна быть в переданном словаре)
    Returns:
        словарь с пересчитанными курсами
    """
    rub_rate = rates.get(base_currency)
    if not isinstance(rub_rate, (int, float)):
        raise ValueError("Курс рубля не передан, невозможно вычислить курсы к RUB")
    rates_in_rub = {
        currency: (round(rub_rate / rate, 2) if isinstance(rate, (int, float)) else "N/A")
        for currency, rate in rates.items()
        if currency != base_currency
    }
    return rates_in_rub
