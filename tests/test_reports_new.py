import json
import pytest
from unittest.mock import patch, Mock
import pandas as pd
from datetime import datetime
from src.reports import get_report_by_category


@pytest.fixture
def mock_data():
    """Фикстура с тестовыми данными DataFrame."""
    return pd.DataFrame(
        {
            "Дата операции": ["01.11.2021 12:00:00", "15.10.2021 18:00:00", "01.01.2021 12:00:00"],
            "Категория": ["Супермаркеты", "Транспорт", "Супермаркеты"],
            "Сумма": [1000, 500, 200],
        }
    )


@patch("src.utils.get_date", return_value="2021-12-31 23:59:59")
@patch("src.utils.filter_dataframe")
@patch("src.reports.get_data")
def test_get_report_by_category_with_valid_date(
    mock_get_data: Mock, mock_filter_dataframe: Mock, mock_get_date: Mock, mock_data
):
    """Тест с переданной датой."""

    # Мокаем get_data
    mock_get_data.return_value = mock_data

    # Мокаем filter_dataframe
    filtered_df = mock_data[mock_data["Категория"] == "Супермаркеты"]
    mock_filter_dataframe.return_value = filtered_df

    # Вызов тестируемой функции
    result = get_report_by_category()

    # Ожидаемый результат
    expected_result = filtered_df.to_json(orient="records", force_ascii=False)

    # Проверяем JSON-ответ
    assert json.loads(result) == json.loads(expected_result)

    # Проверяем вызовы моков
    mock_get_data.assert_called_once()
    mock_filter_dataframe.assert_called_once_with(mock_data, {"Категория": "Супермаркеты"})


@patch("src.utils.get_date", return_value=None)
@patch("src.utils.filter_dataframe")
@patch("src.reports.get_data")
@patch("src.reports.datetime")
def test_get_report_by_category_without_date(
    mock_datetime: Mock, mock_get_data: Mock, mock_filter_dataframe: Mock, mock_get_date: Mock, mock_data
):
    """Тест с отсутствующей датой (используется datetime.now())."""

    # Мокаем datetime.now()
    mock_datetime.now.return_value = datetime(2021, 12, 31, 23, 59, 59)

    # Мокаем get_data
    mock_get_data.return_value = mock_data

    # Мокаем filter_dataframe
    filtered_df = mock_data[mock_data["Категория"] == "Супермаркеты"]
    mock_filter_dataframe.return_value = filtered_df

    # Вызов тестируемой функции
    result = get_report_by_category()

    # Ожидаемый результат
    expected_result = filtered_df.to_json(orient="records", force_ascii=False)

    # Проверяем JSON-ответ
    assert json.loads(result) == json.loads(expected_result)

    # Проверяем вызовы моков
    mock_get_data.assert_called_once()
    mock_filter_dataframe.assert_called_once_with(mock_data, {"Категория": "Супермаркеты"})
    mock_datetime.now.assert_called_once()
