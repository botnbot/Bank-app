from datetime import datetime
from unittest.mock import patch
import pandas as pd
import pytest
from pandas import DataFrame
from pandas.testing import assert_frame_equal

from src.views import get_operations_for_current_month, get_top_5, get_total_spending, sum_by_category


@pytest.fixture
def sample_dataframe() -> DataFrame:
    """Фикстура для создания тестового DataFrame с транзакциями."""
    data = {
        "Дата операции": ["2025-01-10", "2025-01-20", "2025-02-05", "2025-01-25"],
        "Сумма": [100, 200, 300, 400],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    return df


def test_get_operations_current_month_default_date(sample_dataframe: DataFrame) -> None:
    """Тест: фильтрация транзакций за текущий месяц (текущая дата по умолчанию)."""
    current_date = "2025-01-27 00:00:00"
    filtered_df = get_operations_for_current_month(sample_dataframe, current_date)

    expected_data = {
        "Дата операции": ["2025-01-10", "2025-01-20", "2025-01-25"],
        "Сумма": [100, 200, 400],
    }
    expected_df = pd.DataFrame(expected_data)
    expected_df["Дата операции"] = pd.to_datetime(expected_df["Дата операции"])

    assert_frame_equal(filtered_df.reset_index(drop=True), expected_df)


def test_get_operations_current_month_string_date(sample_dataframe: DataFrame) -> None:
    """Тест: фильтрация транзакций за текущий месяц (строка в формате даты)."""
    current_date = "2025-01-27 00:00:00"
    filtered_df = get_operations_for_current_month(sample_dataframe, current_date)
    expected_data = {
        "Дата операции": ["2025-01-10", "2025-01-20", "2025-01-25"],
        "Сумма": [100, 200, 400],
    }
    expected_df = pd.DataFrame(expected_data)
    expected_df["Дата операции"] = pd.to_datetime(expected_df["Дата операции"])
    assert_frame_equal(filtered_df.reset_index(drop=True), expected_df)


def test_get_operations_current_month_datetime_date(sample_dataframe: DataFrame) -> None:
    """Тест: фильтрация транзакций за текущий месяц (объект datetime)."""
    current_date = datetime(2025, 1, 15, 00, 00, 00)
    filtered_df = get_operations_for_current_month(sample_dataframe, current_date)
    expected_data = {
        "Дата операции": ["2025-01-10"],
        "Сумма": [100],
    }
    expected_df = pd.DataFrame(expected_data)
    expected_df["Дата операции"] = pd.to_datetime(expected_df["Дата операции"])

    assert_frame_equal(filtered_df.reset_index(drop=True), expected_df)


def test_get_operations_current_month_cutoff_date(sample_dataframe: DataFrame) -> None:
    """Тест: отсечение транзакций, произошедших после переданной даты."""
    current_date = datetime(2025, 1, 20, 00, 00, 00)
    filtered_df = get_operations_for_current_month(sample_dataframe, current_date)

    expected_data = {
        "Дата операции": ["2025-01-10", "2025-01-20"],
        "Сумма": [100, 200],
    }
    expected_df = pd.DataFrame(expected_data)
    expected_df["Дата операции"] = pd.to_datetime(expected_df["Дата операции"])

    assert_frame_equal(filtered_df.reset_index(drop=True), expected_df)


def test_invalid_date_format(sample_dataframe: DataFrame) -> None:
    """Тест: передача некорректной даты (строка)."""
    with pytest.raises(ValueError, match="Передана некорректная дата: invalid-date"):
        get_operations_for_current_month(sample_dataframe, "invalid-date")


def test_invalid_date_type(sample_dataframe: DataFrame) -> None:
    """Тест: передача недопустимого типа данных в current_date."""
    with pytest.raises(ValueError, match="Аргумент .* должен быть строкой .* объектом datetime или None"):
        get_operations_for_current_month(sample_dataframe, 123)


def test_filter_empty_dataframe() -> None:
    """Тест: передача пустого DataFrame."""
    df = pd.DataFrame(columns=["Дата операции", "Сумма"])
    filtered_df = get_operations_for_current_month(df, "2025-01-27 00:00:00")
    assert filtered_df.empty


def test_sum_by_category_succes() -> None:
    """Тест успешной группировки по категориям"""
    data = {
        "Категория": ["первая", "вторая", "третья", "первая"],
        "Сумма операции с округлением": [100, 200, 300, 400],
    }
    df = pd.DataFrame(data)
    result = sum_by_category(df)

    expected_data = {"Категория": ["вторая", "первая", "третья"], "Сумма операции с округлением": [200, 500, 300]}
    expected_result = pd.DataFrame(expected_data)

    assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))


def test_get_total_spending() -> None:
    """Тест успешной группировки по номерам карт"""
    data = {
        "Номер карты": ["1111", "2222", "4444", "2222"],
        "Сумма операции с округлением": [100, 200, 300, 400],
        "Кэшбэк": [1, 2, 4, 5],
    }
    df = pd.DataFrame(data)

    result = get_total_spending(df)
    expected_data = {
        "Номер карты": ["1111", "2222", "4444"],
        "Сумма операции с округлением": [100, 600, 300],
        "Кэшбэк": [1, 7, 4],
    }
    expected_result = pd.DataFrame(expected_data)
    assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))


def test_get_top_5() -> None:
    """Тест фильтрации Топ-5 транзакций"""
    data = {
        "Дата операции": [
            "2021-25-06",
            "2021-24-06",
            "2021-20-06",
            "2020-25-06",
            "2018-25-06",
            "2020-25-08",
            "2019-25-08",
        ],
        "Сумма операции с округлением": [1600, 16000, 20, 50, 100, 1000, 47],
        "Категория": ["1", "2", "3", "4", "5", "6", "7"],
        "Описание": ["Колхоз", "Ozon.ru", "Константин Л.", "Константин Л.", "Ситидрайв", "РЖД", "Mouse Tail"],
    }
    df = pd.DataFrame(data)
    result = get_top_5(df)

    expected_data = {
        "Дата операции": ["2021-24-06", "2021-25-06", "2020-25-08", "2018-25-06", "2020-25-06"],
        "Сумма операции с округлением": [16000, 1600, 1000, 100, 50],
        "Категория": ["2", "1", "6", "5", "4"],
        "Описание": ["Ozon.ru", "Колхоз", "РЖД", "Ситидрайв", "Константин Л."],
    }
    expected_result = pd.DataFrame(expected_data)
    assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))

import json
from unittest.mock import patch, Mock, mock_open
import pytest

from src.views import main


@patch("src.views.get_data")
@patch("src.views.get_date", return_value="2025-01-15 12:00:00")
@patch("src.views.get_operations_for_current_month")
@patch("src.views.get_total_spending")
@patch("src.views.get_top_5")
@patch("src.views.get_stock_prices", return_value={"AAPL": "150", "TSLA": "700"})
@patch("src.views.get_exchange_rates", return_value={"USD": 92.5, "EUR": 100.1})
@patch("src.views.convert_to_rub", return_value={"USD": 92.5, "EUR": 100.1})
@patch("src.views.greetings", return_value="Добрый день")
def test_main(
    mock_greetings,
    mock_convert_to_rub,
    mock_get_exchange_rates,
    mock_get_stock_prices,
    mock_get_top_5,
    mock_get_total_spending,
    mock_get_operations_for_current_month,
    mock_get_date,
    mock_get_data,
):
    """Тест успешного выполнения main()."""

    # Мокаем данные
    mock_get_data.return_value = [
        {"Дата операции": "2025-01-10 12:00:00", "Номер карты": "1234567890123456", "Сумма операции с округлением": 1000},
        {"Дата операции": "2025-01-20 14:00:00", "Номер карты": "9876543210987654", "Сумма операции с округлением": 1500},
    ]

    mock_get_operations_for_current_month.return_value = mock_get_data.return_value

    mock_get_total_spending.return_value = [
        {"Номер карты": "1234567890123456", "Сумма операции с округлением": 1000, "Кэшбэк": 10},
        {"Номер карты": "9876543210987654", "Сумма операции с округлением": 1500, "Кэшбэк": 15},
    ]

    mock_get_top_5.return_value = [
        {"Дата операции": "2025-01-10", "Сумма операции с округлением": 1000, "Категория": "Магазины", "Описание": "Покупка"},
        {"Дата операции": "2025-01-20", "Сумма операции с округлением": 1500, "Категория": "Развлечения", "Описание": "Кинотеатр"},
    ]

    # Загружаем mock user_settings
    with patch("builtins.open", mock_open(read_data=json.dumps({"user_stocks": ["AAPL", "TSLA"], "user_currencies": ["USD", "EUR"]}))):
        result = main()

    # Преобразуем JSON в объект Python
    result_data = json.loads(result)

    # Проверяем, что greeting формируется корректно
    assert result_data["greeting"] == "Добрый день"

    # Проверяем, что данные по картам корректны
    assert result_data["cards"] == [
        {"last_digits": "3456", "total_spent": 1000, "cashback": 10},
        {"last_digits": "7654", "total_spent": 1500, "cashback": 15},
    ]

    # Проверяем топ-5 транзакций
    assert len(result_data["top_transactions"]) == 2

    # Проверяем валютные курсы
    assert result_data["currency_rates"] == [
        {"currency": "USD", "rate": 92.5},
        {"currency": "EUR", "rate": 100.1},
    ]

    # Проверяем курсы акций
    assert result_data["stock_prices"] == [
        {"stock": "AAPL", "price": "150"},
        {"stock": "TSLA", "price": "700"},
    ]

    # Проверяем, что все методы были вызваны
    mock_get_data.assert_called_once()
    mock_get_date.assert_called_once()
    mock_get_operations_for_current_month.assert_called_once()
    mock_get_total_spending.assert_called_once()
    mock_get_top_5.assert_called_once()
    mock_get_stock_prices.assert_called_once()
    mock_get_exchange_rates.assert_called_once()
    mock_convert_to_rub.assert_called_once()
    mock_greetings.assert_called_once()

