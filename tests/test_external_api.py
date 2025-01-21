from typing import Generator
from unittest.mock import MagicMock, Mock, patch

import pytest

# type: ignore
from finnhub.exceptions import FinnhubAPIException  # type: ignore

from src.external_api import get_stock_prices


@pytest.fixture
def mock_finnhub_client() -> Generator:
    """Мок для клиента Finnhub."""
    with patch("finnhub.Client") as mock_client:
        yield mock_client


def test_get_stock_prices_success(mock_finnhub_client: Mock) -> None:
    """Тест успешного получения цен."""
    mock_instance = MagicMock()
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

    mock_response = MagicMock()
    mock_response.json.return_value = {"error": "API Error"}

    mock_instance = MagicMock()
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

    mock_response = MagicMock()
    mock_response.json.return_value = {"error": "API Error"}

    mock_instance = MagicMock()
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
    mock_instance = MagicMock()
    mock_instance.quote.side_effect = TypeError("Unexpected type error")
    mock_finnhub_client.return_value = mock_instance

    result = get_stock_prices(("AAPL",))
    assert result == {"AAPL": "Неизвестная ошибка: Unexpected type error"}
