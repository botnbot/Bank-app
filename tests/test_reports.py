import json
from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from pandas import DataFrame

from src.reports import get_report_by_category


@pytest.fixture
def mock_data() -> DataFrame:
    """Возвращает тестовый DataFrame с операциями"""
    return pd.DataFrame(
        {
            "Дата операции": ["01.11.2021 12:00:00", "15.10.2021 18:00:00", "01.01.2021 12:00:00"],
            "Категория": ["Супермаркеты", "Транспорт", "Супермаркеты"],
            "Сумма": [1000, 500, 200],
        }
    )


@pytest.fixture
def mock_filtered_data() -> DataFrame:
    """Возвращает тестовый DataFrame после фильтрации"""
    return pd.DataFrame({"Дата операции": ["01.11.2021 12:00:00"], "Категория": ["Супермаркеты"], "Сумма": [1000]})


@patch("builtins.input", return_value="2021-12-31 23:59:59")
@patch("src.utils.get_date")
@patch("src.utils.filter_dataframe")
@patch("src.reports.get_data")
def test_get_report_by_category_with_date(
    mock_get_data: Mock,
    mock_filter_dataframe: Mock,
    mock_get_date: Mock,
    mock_input: Mock,
    mock_data: Mock,
    mock_filtered_data: Mock,
) -> None:
    """Проверяем, что функция корректно работает с переданной датой"""

    mock_get_date.return_value = "2021-12-31 23:59:59"
    mock_get_data.return_value = mock_data
    mock_filter_dataframe.return_value = mock_filtered_data

    result = get_report_by_category()

    expected_result = json.dumps(
        [{"Дата операции": "01.11.2021 12:00:00", "Категория": "Супермаркеты", "Сумма": 1000}],
        ensure_ascii=False,
    )

    assert json.loads(result) == json.loads(expected_result)
    mock_get_data.assert_called_once()


@patch("builtins.input", return_value="")
@patch("src.utils.get_date")
@patch("src.utils.datetime")
@patch("src.utils.filter_dataframe")
@patch("src.reports.get_data")
def test_get_report_by_category_without_date(
    mock_get_data: Mock,
    mock_filter_dataframe: Mock,
    mock_datetime: Mock,
    mock_get_date: Mock,
    mock_input: Mock,
    mock_data: Mock,
    mock_filtered_data: Mock,
) -> None:
    """Проверяем, что при отсутствии даты используется текущая"""

    mock_datetime.now.return_value = datetime(2021, 12, 31, 23, 59, 59)
    mock_get_date.return_value = None
    mock_get_data.return_value = mock_data
    mock_filter_dataframe.return_value = mock_filtered_data

    result = get_report_by_category()

    expected_result = json.dumps(
        [{"Дата операции": "01.11.2021 12:00:00", "Категория": "Супермаркеты", "Сумма": 1000}],
        ensure_ascii=False,
    )

    assert json.loads(result) == json.loads(expected_result)
    mock_get_data.assert_called_once()


@patch("builtins.input", return_value="2021-12-31 23:59:59")
@patch("src.utils.get_date")
@patch("src.reports.get_data")
def test_get_report_by_category_filters_by_date(
    mock_get_data: Mock, mock_get_date: Mock, mock_input: Mock, mock_data: Mock
) -> None:
    """Проверяем, что старые данные не попадают в отчет"""

    mock_get_date.return_value = "2021-12-31 23:59:59"
    mock_data.loc[len(mock_data)] = ["01.06.2021 12:00:00", "Супермаркеты", 500]
    mock_get_data.return_value = mock_data

    result = get_report_by_category()
    parsed_result = json.loads(result)

    assert all(
        datetime.strptime(entry["Дата операции"], "%d.%m.%Y %H:%M:%S") >= datetime(2021, 10, 1, 0, 0, 0)
        for entry in parsed_result
    )
