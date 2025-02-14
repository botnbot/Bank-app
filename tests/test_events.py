import json
import logging
from typing import Generator
from unittest.mock import Mock, mock_open, patch

import pandas as pd
import pytest

from src.events import events


@pytest.fixture(scope="function", autouse=True)
def disable_logging() -> Generator:
    """Отключает логирование на время тестов."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def mock_events_env() -> Generator:
    with (
        patch("src.utils.get_data") as mock_get_data,
        patch("src.utils.get_df_for_current_period") as mock_get_df,
        patch("builtins.open", mock_open(read_data=json.dumps({"user_stocks": ["AAPL"], "user_currencies": ["USD"]}))),
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
        mock_get_data.return_value = mock_df
        mock_get_df.return_value = mock_df

        # Эмулируем успешный ответ API
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "rates": {"USD": 1.1, "RUB": 99}}
        mock_requests_get.return_value = mock_response

        yield


def test_events(mock_events_env: Mock) -> None:
    """Тест для функции events()."""
    with (
        patch("src.events.get_stock_prices", return_value={"AAPL": 150}) as mock_get_stock_prices,
        patch("src.events.convert_to_rub", return_value={"USD": 90}) as mock_convert_to_rub,
    ):

        result_json = events("2024-02-05 12:00:00", "W")
        result = json.loads(result_json)

        # Проверяем структуру курсов валют
        assert result["currency_rates"] == [{"currency": "USD", "rate": 90}]
        assert result["currency_rates"][0]["currency"] == "USD"
        assert result["currency_rates"][0]["rate"] == 90
        mock_get_stock_prices.assert_called_once()  # Проверяем вызов функции

        # Проверяем структуру курсов акций
        assert result["stock_prices"] == [{"stock": "AAPL", "price": 150}]
        assert result["stock_prices"][0]["stock"] == "AAPL"
        assert result["stock_prices"][0]["price"] == 150
        mock_convert_to_rub.assert_called_once()

        # Проверяем, что все ключи есть в результате
        assert "expenses" in result
        assert "income" in result
        assert "currency_rates" in result
        assert "stock_prices" in result

    # Проверяем обработку исключений при получении курсов акций
    with patch("src.external_api.get_stock_prices", side_effect=Exception("Ошибка API")):
        result_json = events("2024-02-05 12:00:00")
        result = json.loads(result_json)
        assert result["stock_prices"] == []  # Ошибка API должна приводить к пустому списку

    # Проверяем обработку исключений при получении курсов валют
    with patch("src.external_api.get_exchange_rates", side_effect=Exception("Ошибка API")):
        result_json = events("2024-02-05 12:00:00")
        result = json.loads(result_json)
        assert result["currency_rates"] == [{"currency": "USD", "rate": 90.0}]
