import os
from typing import Generator
from unittest.mock import Mock, patch

import pytest
from finnhub.exceptions import FinnhubAPIException  # type: ignore

from src.external_api import convert_to_rub, get_exchange_rates, get_stock_prices


@pytest.fixture
def mock_finnhub_client() -> Generator:
    """Мок для клиента Finnhub."""
    with patch("finnhub.Client") as mock_client:
        yield mock_client


@pytest.fixture(autouse=True)
def set_env_variables(monkeypatch: Mock) -> None:
    """Фикстура для задания переменной окружения API_KEY."""
    monkeypatch.setenv("API_KEY", "test_api_key")


def test_get_stock_prices_success(mock_finnhub_client: Mock) -> None:
    """Тест успешного получения цен акций."""
    mock_instance = Mock()
    mock_instance.quote.side_effect = [
        {"c": 150.00},  # Ответ для AAPL
        {"c": 2800.00},  # Ответ для GOOGL
    ]
    mock_finnhub_client.return_value = mock_instance

    result = get_stock_prices(("AAPL", "GOOGL"))
    assert result == {"AAPL": 150.00, "GOOGL": 2800.00}


def test_get_stock_prices_with_error(mock_finnhub_client: Mock) -> None:
    """Тест обработки ошибок для одного из тикеров."""
    from finnhub.exceptions import FinnhubAPIException

    mock_response = Mock()
    mock_response.json.return_value = {"error": "API Error"}

    mock_instance = Mock()
    mock_instance.quote.side_effect = [
        {"c": 150.00},  # Ответ для AAPL
        FinnhubAPIException(mock_response),  # Ошибка для GOOGL
    ]
    mock_finnhub_client.return_value = mock_instance

    result = get_stock_prices(("AAPL", "GOOGL"))
    assert result == {
        "AAPL": 150.00,
        "GOOGL": "Ошибка API {'error': 'API Error'}",
    }


def test_get_stock_prices_mixed_responses(mock_finnhub_client: Mock) -> None:
    """Тест смешанных ответов: успешный, некорректный, ошибка."""

    mock_response = Mock()
    mock_response.json.return_value = {"error": "API Error"}

    mock_instance = Mock()
    mock_instance.quote.side_effect = [
        {"c": 150.00},  # Ответ для AAPL
        {},  # Некорректный ответ для GOOGL
        FinnhubAPIException(mock_response),  # Ошибка для MSFT
    ]
    mock_finnhub_client.return_value = mock_instance

    result = get_stock_prices(("AAPL", "GOOGL", "MSFT"))
    assert result == {
        "AAPL": 150.00,
        "GOOGL": "Ошибка API Некорректный ответ API для тикера GOOGL",
        "MSFT": "Ошибка API {'error': 'API Error'}",
    }


def test_get_stock_prices_unknown_exception(mock_finnhub_client: Mock) -> None:
    """Тест обработки неизвестной ошибки."""
    mock_instance = Mock()
    mock_instance.quote.side_effect = TypeError("Unexpected type error")
    mock_finnhub_client.return_value = mock_instance

    result = get_stock_prices(("AAPL",))
    assert result == {"AAPL": "Неизвестная ошибка: Unexpected type error"}


@patch("requests.get")
def test_get_exchange_rates_success(mock_get: Mock) -> None:
    """Тест успешного получения обменных курсов"""
    mock_response = Mock()
    mock_response.json.return_value = {"success": True, "rates": {"RUB": 75.0, "USD": 1.1}}
    mock_get.return_value = mock_response

    result = get_exchange_rates(("USD",))
    assert result == {"USD": 1.1, "RUB": 75.0}
    mock_get.assert_called_once_with(
        "https://data.fixer.io/api/latest?access_key=test_api_key", params={"base": "EUR", "symbols": "USD,RUB"}
    )


def test_get_exchange_rates_missing_api_key() -> None:
    """Тест исключения при отсутствии API-ключа."""
    # Подменяем os.getenv с помощью patch
    with patch("os.getenv", lambda key: None if key == "API_KEY" else os.getenv(key)):
        # Проверяем, что os.getenv возвращает None для API_KEY
        assert os.getenv("API_KEY") is None

        # Ожидаем, что функция выбросит ValueError
        with pytest.raises(ValueError, match="API-ключ не найден"):
            get_exchange_rates(("USD",))


@patch("requests.get")
def test_get_exchange_rates_wrong_api_key(mock_get: Mock, monkeypatch: Mock) -> None:
    """Тест исключения при неверном API-ключе."""
    monkeypatch.setenv("API_KEY", "")  # Устанавливаем API_KEY как пустую строку

    with pytest.raises(ValueError, match="API-ключ не найден"):
        get_exchange_rates(("USD",))


@patch("requests.get")
def test_get_exchange_rates_api_error(mock_get: Mock) -> None:
    """Тест ошибки получения ключа API."""
    mock_response = Mock()
    mock_response.json.return_value = {"success": False, "error": {"info": "Invalid API key."}}
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="Ошибка API: Invalid API key."):
        get_exchange_rates(("USD",))


@patch("requests.get")
def test_get_exchange_rates_missing_rub(mock_get: Mock) -> None:
    """Тест отсутствия курса RUB в запросе."""
    mock_response = Mock()
    mock_response.json.return_value = {"success": True, "rates": {"RUB": 75.0, "USD": 1.1}}
    mock_get.return_value = mock_response

    result = get_exchange_rates(("USD",))
    assert "RUB" in result
    assert result["RUB"] == 75.0


@patch("requests.get")
def test_get_exchange_rates_missing_currency_code(mock_get: Mock) -> None:
    """Тест запроса курса несуществующей валюты."""
    mock_response = Mock()
    mock_response.json.return_value = {"success": True, "rates": {"RUB": 75.0}}
    mock_get.return_value = mock_response

    result = get_exchange_rates(("USD",))
    assert result == {"USD": "N/A", "RUB": 75.0}


def test_convert_to_rub_success() -> None:
    """Тест успешного пересчета курса в рубли"""
    rates = {"USD": 1.10, "EUR": 1, "RUB": 115}
    result = convert_to_rub(rates)
    assert result == {"USD": 104.55, "EUR": 115}


def test_convert_to_rub_invalid_currency_value() -> None:
    """Тест передачи неверного курса валюты"""
    rates = {"USD": "N/A", "EUR": 1, "RUB": 115}
    result = convert_to_rub(rates)
    assert result == {"USD": "N/A", "EUR": 115}


def test_convert_to_rub_missing_rub_rate() -> None:
    """Тест отсутствия курса рубля"""
    rates = {"USD": 1.10, "EUR": 1}
    with pytest.raises(ValueError, match="Курс рубля не передан, невозможно вычислить курсы к RUB"):
        convert_to_rub(rates)
