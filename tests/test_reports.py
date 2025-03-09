import json
import logging
import os
from datetime import datetime
from typing import Any, Callable, Generator
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from _pytest.logging import LogCaptureFixture
from freezegun import freeze_time

from config import ROOT_PATH


@pytest.fixture(scope="function", autouse=True)
def disable_logging() -> Generator:
    """Отключает логирование на время тестов."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def mock_data() -> pd.DataFrame:
    """Возвращает тестовый DataFrame с операциями"""
    return pd.DataFrame(
        {
            "Дата операции": ["01.11.2021 12:00:00", "15.10.2021 18:00:00", "01.01.2021 12:00:00"],
            "Категория": ["Супермаркеты", "Транспорт", "Супермаркеты"],
            "Сумма": [1000, 500, 200],
        }
    )


@pytest.fixture
def mock_filtered_data() -> pd.DataFrame:
    """Возвращает тестовый DataFrame после фильтрации"""
    return pd.DataFrame({"Дата операции": ["01.11.2021 12:00:00"], "Категория": ["Супермаркеты"], "Сумма": [1000]})


def mock_save_to_file(*args: Any, **kwargs: Any) -> Callable:
    """Mock-декоратор для подмены @save_to_file"""

    def wrapper(func: Callable) -> Callable:
        return func

    return wrapper


with patch("src.decorators.save_to_file", Mock(side_effect=mock_save_to_file)) as mock_decorator:
    from src.reports import get_report_by_category


@patch("src.utils.filter_dataframe")
@patch("src.reports.get_data")
@patch("os.path.exists", return_value=True)
def test_get_report_by_category_with_date(
    mock_exists: Mock,
    mock_get_data: Mock,
    mock_filter_dataframe: Mock,
    mock_data: pd.DataFrame,
    mock_filtered_data: pd.DataFrame,
) -> None:
    """Проверяем, что функция корректно работает с переданной датой и аргументами"""

    mock_get_data.return_value = mock_data
    mock_filter_dataframe.return_value = mock_filtered_data
    expected_path = os.path.join(ROOT_PATH, "test_data.csv")

    result = get_report_by_category("test_data.csv", "Супермаркеты", "2021-12-31 23:59:59")

    expected_result = json.dumps(
        [{"Дата операции": "01.11.2021 12:00:00", "Категория": "Супермаркеты", "Сумма": 1000}],
        ensure_ascii=False,
    )

    assert json.loads(result) == json.loads(expected_result)
    mock_get_data.assert_called_once_with(expected_path)


@patch("src.utils.filter_dataframe")
@patch("src.reports.get_data")
@patch("os.path.exists", return_value=True)
@freeze_time("2021-12-31 23:59:59")
def test_get_report_by_category_without_date(
    mock_exists: Mock,
    mock_get_data: Mock,
    mock_filter_dataframe: Mock,
    mock_data: pd.DataFrame,
    mock_filtered_data: pd.DataFrame,
) -> None:
    """Проверяем, что при отсутствии даты используется текущая дата"""

    mock_get_data.return_value = mock_data
    mock_filter_dataframe.return_value = mock_filtered_data
    expected_path = os.path.join(ROOT_PATH, "test_data.csv")

    result = get_report_by_category("test_data.csv", "Супермаркеты")

    expected_result = json.dumps(
        [{"Дата операции": "01.11.2021 12:00:00", "Категория": "Супермаркеты", "Сумма": 1000}],
        ensure_ascii=False,
    )

    assert json.loads(result) == json.loads(expected_result)
    mock_get_data.assert_called_once_with(expected_path)


def test_get_report_by_category_invalid_date() -> None:
    """Тест некорректной даты"""
    invalid_date = "2023/10/05 12:34:56"
    with pytest.raises(ValueError) as e:
        get_report_by_category("test_data.csv", "Супермаркеты", invalid_date)
    assert str(e.value) == ("Некорректный формат даты, используйте 'YYYY-MM-DD HH:MM:SS'")


@patch("os.path.exists", return_value=True)
@patch("src.utils.get_date")
@patch("src.reports.get_data")
@freeze_time("2021-12-31 23:59:59")
def test_get_report_by_category_filters_by_date(
    mock_get_data: Mock,
    mock_get_date: Mock,
    mock_exists: Mock,
) -> None:
    """Проверяем, что старые даты не попадают в отчет"""

    mock_get_date.return_value = "2021-12-31 23:59:59"

    mock_data = pd.DataFrame(
        [
            ["01.06.2021 12:00:00", "Супермаркеты", 500],
            ["02.10.2021 12:00:00", "Супермаркеты", 600],
            ["15.11.2021 14:30:00", "Супермаркеты", 1500],
        ],
        columns=["Дата операции", "Категория", "Сумма"],
    )

    mock_get_data.return_value = mock_data

    result = get_report_by_category("test_data.csv", "Супермаркеты")
    parsed_result = json.loads(result)

    assert all(
        datetime.strptime(entry["Дата операции"], "%d.%m.%Y %H:%M:%S") >= datetime(2021, 10, 1, 0, 0, 0)
        for entry in parsed_result
    )


@patch("src.reports.get_data", side_effect=FileNotFoundError("Файл с данными не найден"))
@patch("src.reports.loger.error")
def test_log_error_when_file_not_found(mock_log_error: Mock, mock_get_data: Mock) -> None:
    """Тестирует логирование ошибки, когда файл не найден."""

    with pytest.raises(FileNotFoundError, match="Файл с данными не найден"):
        get_report_by_category("test_data.csv", "JYH")
    mock_log_error.assert_called_with("Ошибка доступа к файлу с данными: Файл с данными не найден")


def test_logging_permission_error(caplog: LogCaptureFixture) -> None:
    with patch("os.makedirs"), patch("logging.FileHandler", side_effect=PermissionError("No permission")):
        from src.reports import loger

        loger.handlers.clear()
        with caplog.at_level(logging.ERROR, logger="reports"):
            from importlib import reload

            from src import reports

            reload(reports)
        assert "Ошибка доступа к файлу логов" in caplog.text
