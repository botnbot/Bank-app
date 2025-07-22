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
def mock_views_env() -> Generator:
    mock_settings = json.dumps({"user_stocks": ["AAPL"], "user_currencies": ["USD", "EUR"]})

    with (
        patch("builtins.open", mock_open(read_data=mock_settings)),
        patch("src.views.pd.read_excel") as mock_read_excel,
        patch("requests.get") as mock_requests_get,
    ):
        # Подготовка данных
        mock_df = pd.DataFrame(
            {
                "Дата операции": ["2024-02-01 10:00:00", "2024-02-05 10:30:00"],
                "Сумма операции с округлением": [10, 999],
                "Сумма операции": [10, 999],
                "Кэшбэк": [6, None],
                "Категория": ["Продукты", "Зарплата"],
                "Номер карты": ["12588", "987654"],
                "Описание": ["Ozon.ru", "Магнит"],
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
    from src.views import views


@pytest.mark.parametrize(
    "expected_keys",
    [
        (["greeting", "cards", "currency_rates", "stock_prices", "top_transactions"]),
    ],
)
def test_views_success(mock_views_env: None, expected_keys: list) -> None:
    """
    Тест успешного выполнения функции views().
    """
    with (
        patch("src.views.get_stock_prices", return_value={"AAPL": 150}) as mock_get_stock_prices,
        patch("src.views.convert_to_rub", return_value={"USD": 90}) as mock_convert_to_rub,
    ):
        result_json = views("2024-02-05 12:00:00")
        result = json.loads(result_json)

        # Проверяем структуру курсов валют
        assert result["currency_rates"] == [{"currency": "USD", "rate": 90}]
        mock_get_stock_prices.assert_called_once()

        # Проверяем структуру курсов акций
        assert result["stock_prices"] == [{"stock": "AAPL", "price": 150}]
        mock_convert_to_rub.assert_called_once()

        # Проверяем, что все ключи есть в результате
        assert all(key in result for key in expected_keys)


@pytest.mark.usefixtures("disable_logging")
def test_views_currency_exception() -> None:
    """Тест обработки исключения при получении курсов валют."""
    test_date = "2025-01-01 22:22:22"
    test_currency = ["USD", "EUR"]
    mock_settings = json.dumps({"user_stocks": [], "user_currencies": test_currency})

    # Мокаем нужный DataFrame
    mock_df = pd.DataFrame(
        {

            "Дата операции": ["2025-01-01 10:00:00", "2025-01-01 10:30:00"],
            "Сумма операции с округлением": [10, 999],
            "Сумма операции": [10, 999],
            "Кэшбэк": [6, None],
            "Категория": ["Продукты", "Зарплата"],
            "Номер карты": ["12588", "987654"],
            "Описание": ["Ozon.ru", "Магнит"],
        }
    )
    mock_df["Дата операции"] = pd.to_datetime(mock_df["Дата операции"])

    with (
        patch("src.views.open", mock_open(read_data=mock_settings)),
        patch("src.views.get_exchange_rates", side_effect=Exception("API error")),
        patch("src.views.convert_to_rub", return_value={}),
        patch("src.views.pd.read_excel", return_value=mock_df),
    ):
        result_json = views(test_date)
        result = json.loads(result_json)

        expected_rates = [{"currency": cur, "rate": "API error"} for cur in test_currency]
        assert result["currency_rates"] == expected_rates


@patch("src.views.get_stock_prices")
@patch("src.views.get_exchange_rates")
def test_views_continues_after_errors(mock_get_exchange_rates: Mock, mock_get_stock_prices: Mock, mock_views_env: None) -> None:
    """
    Тест продолжения работы функции после возникновения исключения
    """
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

    result_json = views("2024-02-05 12:00:00")
    result = json.loads(result_json)

    assert result["stock_prices"] == [
        {"stock": "AAPL", "price": 150},
        {"stock": "GOOGL", "price": 2800},
        {"stock": "TSLA", "price": "Ошибка API"},
    ]
    assert result["currency_rates"] == [
        {"currency": "EUR", "rate": 110},
        {"currency": "UU", "rate": "N/A"},
    ]

    assert "error" not in result  # Если функция возвращает ошибки в JSON, проверяем их отсутствие


@patch("src.views.loger.warning")
@patch("src.views.loger.error")
def test_views_logging_errors(mock_log_error: Mock, mock_log_warning: Mock, mock_views_env: None) -> None:
    """Тест проверки логирования ошибок и предупреждений."""
    with (
        patch("src.views.get_exchange_rates", side_effect=Exception("Ошибка получения курса валют")),
        patch("src.views.get_stock_prices", side_effect=Exception("Ошибка получения курса акций")),
    ):
        views("2024-02-05 12:00:00")

    mock_log_warning.assert_any_call("Ошибка при получении курсов валют: Ошибка получения курса валют")
    mock_log_error.assert_any_call(
        "Неизвестная ошибка при получении курсов акций: Exception('Ошибка получения курса акций')"
    )
