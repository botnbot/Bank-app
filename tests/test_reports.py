from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd

from src.reports import get_report_by_category


@patch("src.reports.get_data")
@patch("src.reports.filter_dataframe")
@patch("src.reports.datetime")
def test_get_report_by_category_with_valid_date(
    mock_datetime: Mock, mock_filter_dataframe: Mock, mock_get_data: Mock
) -> None:
    """Успешный тест с корректной датой."""

    # Мокаем текушую дату
    mock_datetime.now.return_value = datetime(2021, 12, 31, 23, 59, 59)
    mock_datetime.strptime = datetime.strptime  # For correct strptime behavior

    # Мокаем get_data
    mock_df = pd.DataFrame(
        {
            "Дата операции": ["01.11.2021 12:00:00", "15.10.2021 18:00:00", "01.01.2021 12:00:00"],
            "Категория": ["Супермаркеты", "Транспорт", "Супермаркеты"],
            "Сумма": [1000, 500, 200],
        }
    )
    mock_get_data.return_value = mock_df

    # Мокаем filter_dataframe
    filtered_df = pd.DataFrame(
        {"Дата операции": ["01.11.2021 12:00:00"], "Категория": ["Супермаркеты"], "Сумма": [1000]}
    )
    mock_filter_dataframe.return_value = filtered_df

    # Вызов функции
    result = get_report_by_category("mock_path", "Супермаркеты", "2021-12-31 23:59:59")

    # Ожидаемый результат
    expected_result = '[{"Дата операции":"01.11.2021 12:00:00","Категория":"Супермаркеты","Сумма":1000}]'

    # Проверяем
    assert result == expected_result

    # Готовим DataFrame для filter_dataframe и удаляем временную колонку
    expected_mock_df = mock_df.copy()
    expected_mock_df["Дата операции временная"] = pd.to_datetime(
        expected_mock_df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce"
    )
    expected_mock_df = expected_mock_df[
        (expected_mock_df["Дата операции временная"] >= datetime(2021, 9, 30, 23, 59, 59))
        & (expected_mock_df["Дата операции временная"] <= datetime(2021, 12, 31, 23, 59, 59))
    ]
    expected_mock_df = expected_mock_df.drop(columns=["Дата операции временная"])

    # Проверяем, что get_data была вызвана с корректным аргументом.
    mock_get_data.assert_called_once_with("mock_path")

    assert mock_filter_dataframe.call_args[0][1] == {"Категория": "Супермаркеты"}


@patch("src.reports.get_data")
@patch("src.reports.filter_dataframe")
@patch("src.reports.datetime")
def test_get_report_by_category_without_optional_date(
    mock_datetime: Mock, mock_filter_dataframe: Mock, mock_get_data: Mock
) -> None:
    """Тест с неуказанной датой (используем текущую)"""

    # Мокаем текущую дату
    mock_datetime.now.return_value = datetime(2021, 12, 31, 23, 59, 59)

    # Мокаем входные данные DataFrame
    mock_df = pd.DataFrame(
        {
            "Дата операции": ["01.11.2021 12:00:00", "15.10.2021 18:00:00", "01.01.2021 12:00:00"],
            "Категория": ["Супермаркеты", "Транспорт", "Супермаркеты"],
            "Сумма": [1000, 500, 200],
        }
    )
    mock_get_data.return_value = mock_df

    # Мокаем результат фильтрации по категории
    filtered_df = pd.DataFrame(
        {"Дата операции": ["01.11.2021 12:00:00"], "Категория": ["Супермаркеты"], "Сумма": [1000]}
    )
    mock_filter_dataframe.return_value = filtered_df

    # Вызов тестируемой функции
    result = get_report_by_category("mock_path", "Супермаркеты")

    # Ожидаемый результат
    expected_result = '[{"Дата операции":"01.11.2021 12:00:00","Категория":"Супермаркеты","Сумма":1000}]'

    # Проверяем результат
    assert result == expected_result


@patch("src.reports.get_data")
@patch("src.reports.filter_dataframe")
@patch("src.reports.datetime")
def test_get_report_by_category_empty_result(
    mock_datetime: Mock, mock_filter_dataframe: Mock, mock_get_data: Mock
) -> None:
    """Тест, когда нет транзакций в указанную дату."""

    # Mock текущую дату
    mock_datetime.now.return_value = datetime(2021, 12, 31, 23, 59, 59)

    # Мокируем входные данные DataFrame
    mock_df = pd.DataFrame(
        {
            "Дата операции": ["01.11.2021 12:00:00", "15.10.2021 18:00:00"],
            "Категория": ["Транспорт", "Транспорт"],
            "Сумма": [500, 300],
        }
    )
    mock_get_data.return_value = mock_df

    # Мокируем результат фильтрации по категории (пустой результат)
    filtered_df = pd.DataFrame(columns=["Дата операции", "Категория", "Сумма"])
    mock_filter_dataframe.return_value = filtered_df

    # Вызов тестируемой функции
    result = get_report_by_category("mock_path", "Супермаркеты")

    # Ожидаемый результат
    expected_result = "[]"

    # Проверяем результат
    assert result == expected_result
