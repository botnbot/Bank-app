import os

import finnhub  # type: ignore
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("apikey")


def get_stock_prices(symbols: tuple) -> dict:
    """Функция принимает кортеж с названиями акций и возвращает словарь, где ключи - тикеры, а значения это их цены"""
    finnhub_client = finnhub.Client(api_key=api_key)
    prices = {}
    for symbol in symbols:
        try:
            quote = finnhub_client.quote(symbol)

            if not quote or "c" not in quote:
                raise ValueError(f"Некорректный ответ API для тикера {symbol}")

            prices[symbol] = quote["c"]

        except finnhub.exceptions.FinnhubAPIException as e:
            prices[symbol] = f"Ошибка API {e}"
        except ValueError as e:
            prices[symbol] = f"Ошибка {e}"
        except Exception as e:
            prices[symbol] = f"Неизвестная ошибка: {e}"

    return prices


def get_exchange_rates(currency_codes: tuple = ("RUB",)) -> dict:
    """Функция принимает кортеж с кодами валют и возвращает словарь, где ключи это коды валют, а значения - это курсы
    этих валют"""

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
    Пересчитывает курсы валют в значения относительно рубля.
    Возвращает словарь, где ключ — это код валюты, а значение — это количество рублей за единицу валюты.
    """
    rub_rate = rates.get(base_currency)
    if not isinstance(rub_rate, (int, float)):
        raise ValueError(f"Курс {base_currency} отсутствует или некорректен: {rub_rate}")

    # Пересчет курсов валют в рубли
    rates_in_rub = {
        currency: (round(rub_rate / rate, 2) if isinstance(rate, (int, float)) else "N/A")
        for currency, rate in rates.items()
        if currency != base_currency  # Исключаем базовую валюту
    }

    return rates_in_rub


if __name__ == "__main__":
    tikers = ("AAPL", "TSLA")
    print(get_stock_prices(tikers))

    currency = ("USD", "GBP", "EUR", "JPY")
    try:
        # Получение курсов валют
        rates = get_exchange_rates(currency)
        # Пересчет курсов относительно рубля
        rates_in_rub = convert_to_rub(rates)
        print(rates_in_rub)
    except ValueError as e:
        print(f"Ошибка: {e}")
