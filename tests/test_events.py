import json
import logging
from typing import Any, Callable, Generator
from unittest.mock import Mock, mock_open, patch

import pandas as pd
import pytest


@pytest.fixture(scope="function", autouse=True)
def disable_logging() -> Generator:
    """Отключает логирование на время тестов."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def mock_events_env() -> Generator:
    mock_settings = json.dumps({"user_stocks": ["AAPL"], "user_currencies": ["USD", "EUR"]})
    with (
        patch("builtins.open", mock_open(read_data=mock_settings)),
        patch("pandas.read_excel") as mock_read_excel,
        patch("requests.get") as mock_requests_get,
    ):
        # Подготовка данных
        mock_df = pd.DataFrame(
            {
                "Дата операции": ["2024-02-01 10:00:00", "2024-02-05 10:30:00"],
                "Сумма платежа": [-1500, 2000],
                "Категория": ["Продукты", "Зарплата"],
            }
        )
        mock_df["Дата операции"] = pd.to_datetime(mock_df["Дата операции"])
        mock_read_excel.return_value = mock_df  # Подменяем чтение Excel-файла
        yield

    mock_requests_get.return_value.json.return_value = {"success": True}  # API должен возвращать данные


def mock_save_to_file(*args: Any, **kwargs: Any) -> Callable:
    """Mock-декоратор для подмены @save_to_file"""

    def wrapper(func: Callable) -> Callable:
        return func

    return wrapper


with patch("src.decorators.save_to_file", Mock(side_effect=mock_save_to_file)) as mock_decorator:
    from src.views import events


@pytest.mark.parametrize(
    "expected_keys",
    [
        (["expenses", "income", "currency_rates", "stock_prices"]),
    ],
)
def test_events_success(mock_events_env: Mock, expected_keys: list) -> None:
    """
    Тест успешного выполнения функции events().
    """
    with (
        patch("src.views.get_stock_prices", return_value={"AAPL": 150}) as mock_get_stock_prices,
        patch("src.views.convert_to_rub", return_value={"USD": 90, "EUR": 100}) as mock_convert_to_rub,
    ):
        result_json = events("2024-02-05 12:00:00", "W")
        result = json.loads(result_json)

        # Проверяем структуру курсов валют
        assert result["currency_rates"] == [{"currency": "USD", "rate": 90}, {"currency": "EUR", "rate": 100}]
        mock_get_stock_prices.assert_called_once()

        # Проверяем структуру курсов акций
        assert result["stock_prices"] == [{"stock": "AAPL", "price": 150}]
        mock_convert_to_rub.assert_called_once()

        # Проверяем, что все ключи есть в результате
        assert all(key in result for key in expected_keys)


def test_events_currency_exception() -> None:
    """Тест обработки исключения при получении курсов валют."""
    test_date = "2025-01-01 22:22:22"
    test_currency = ["USD", "EUR"]

    # Подменяем `get_exchange_rates`, чтобы он всегда вызывал исключение
    with patch("src.views.get_exchange_rates", side_effect=Exception("API error")):
        with patch("src.views.convert_to_rub", return_value={}):
            result_json = events(test_date)
            result = json.loads(result_json)

            # Проверяем, что список `currency_rates` содержит ошибки
            expected_rates = [{"currency": cur, "rate": "API error"} for cur in test_currency]
            assert result["currency_rates"] == expected_rates


@patch("src.views.get_stock_prices")
@patch("src.views.get_exchange_rates")
def test_events_continues_after_errors(mock_get_exchange_rates: Mock, mock_get_stock_prices: Mock) -> None:
    """
    Тест продолжения работы функции после возникновения исключения
    """
    # Настраиваем моки
    mock_get_stock_prices.return_value = {
        "AAPL": 150,
        "GOOGL": 2800,
        "TSLA": "Ошибка API",  # Эмулируем ошибку
    }
    mock_get_exchange_rates.return_value = {
        "EUR": 1.0,
        "UU": "N/A",  # Эмулируем ошибку
        "RUB": 110,
    }

    # Вызываем функцию events
    result_json = events("2024-02-05 12:00:00")
    result = json.loads(result_json)

    # Проверяем, что функция корректно обработала ошибки и вернула данные
    assert result["stock_prices"] == [
        {"stock": "AAPL", "price": 150},
        {"stock": "GOOGL", "price": 2800},
        {"stock": "TSLA", "price": "Ошибка API"},  # Ожидаем, что ошибка будет в результате
    ]
    assert result["currency_rates"] == [
        {"currency": "EUR", "rate": 110},
        {"currency": "UU", "rate": "N/A"},  # Ожидаем, что ошибка будет в результате
    ]

    assert "error" not in result  # Если функция возвращает ошибки в JSON, проверяем их отсутствие


@patch("src.views.loger.warning")
@patch("src.views.loger.error")
def test_events_logging_errors(mock_log_error: Mock, mock_log_warning: Mock) -> None:
    """Тест проверки логирования ошибок и предупреждений."""
    with (
        patch("src.views.get_exchange_rates", side_effect=Exception("Ошибка получения курса валют")),
        patch("src.views.get_stock_prices", side_effect=Exception("Ошибка получения курса акций")),
    ):
        events("2024-02-05 12:00:00")

    mock_log_warning.assert_any_call("Ошибка при получении курсов валют: Ошибка получения курса валют")
    mock_log_error.assert_any_call(
        "Неизвестная ошибка при получении курсов акций: Exception('Ошибка получения курса акций')"
    )
