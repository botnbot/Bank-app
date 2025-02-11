import json
import logging
from typing import Generator
from unittest.mock import Mock, mock_open, patch

import pandas as pd
import pytest

from src.events import events


@pytest.fixture
def mock_events_env() -> Generator:
    with patch("config.ROOT_PATH", "test_root"), patch("src.utils.get_data") as mock_get_data, patch(
        "src.utils.get_df_for_current_period"
    ) as mock_get_df, patch("src.external_api.get_stock_prices") as mock_get_stock_prices, patch(
        "src.external_api.get_exchange_rates"
    ) as mock_get_exchange_rates, patch(
        "src.external_api.convert_to_rub"
    ) as mock_convert_to_rub, patch(
        "builtins.open", mock_open(read_data=json.dumps({"user_stocks": ["AAPL"], "user_currencies": ["USD"]}))
    ), patch(
        "os.makedirs"
    ), patch(
        "pandas.read_excel"
    ) as mock_read_excel:

        # Отключаем логирование для всех логгеров
        logging.disable(logging.CRITICAL)

        # Создаём поддельный DataFrame
        mock_df = pd.DataFrame(
            {
                "Дата операции": ["2024-02-01 10:00:00", "2024-02-05 10:30:00"],
                "Сумма платежа": [-1500, 2000],
                "Категория": ["Продукты", "Зарплата"],
            }
        )
        mock_df["Дата операции"] = pd.to_datetime(mock_df["Дата операции"])  # Преобразуем в datetime

        mock_read_excel.return_value = mock_df  # Подменяем чтение Excel-файла
        mock_get_data.return_value = mock_df
        mock_get_df.return_value = mock_df
        mock_get_stock_prices.return_value = {"AAPL": 150}
        mock_get_exchange_rates.return_value = {"USD": 1.1}
        mock_convert_to_rub.return_value = {"USD": 90}

        yield

        logging.disable(logging.NOTSET) # Включаем логирование обратно


def test_events(mock_events_env: Mock) -> None:
    result_json = events("2024-02-05 12:00:00", "M")
    result = json.loads(result_json)
    assert "expenses" in result
    assert "income" in result
    assert result["expenses"]["total_amount"] == -1500
    assert result["income"]["total_amount"] == 2000
    assert "currency_rates" in result
    assert "stock_prices" in result

    # Проверяем корректность курсов валют
    assert isinstance(result["currency_rates"], list)
    if result["currency_rates"]:
        assert result["currency_rates"][0]["currency"] == "USD"
        assert result["currency_rates"][0]["rate"] == 90

    # Проверяем корректность информации о курсах акций
    assert isinstance(result["stock_prices"], list)
    if result["stock_prices"]:
        assert result["stock_prices"][0]["stock"] == "AAPL"
        assert result["stock_prices"][0]["price"] == 150

    # Проверяем обработку исключений при получении курсов акций
    with patch("src.external_api.get_stock_prices", side_effect=Exception("Ошибка API")):
        result_json = events("2024-02-05 12:00:00")
        result = json.loads(result_json)
        assert result["stock_prices"] == []  # Ошибка API должна приводить к пустому списку

    # Проверяем обработку исключений при получении курсов валют
    with patch("src.external_api.get_exchange_rates", side_effect=Exception("Ошибка API")):
        result_json = events("2024-02-05 12:00:00")
        result = json.loads(result_json)
        assert result["currency_rates"] == []  # Ошибка API должна приводить к пустому списку
