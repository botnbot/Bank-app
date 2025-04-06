import logging
from datetime import datetime
from typing import Any, Callable, Generator
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest
from _pytest.logging import LogCaptureFixture
from freezegun import freeze_time
from pandas._testing import assert_frame_equal


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
            "Сумма операции": [-1000, -500, -200],
        }
    )


@pytest.fixture
def mock_filtered_data() -> pd.DataFrame:
    """Возвращает тестовый DataFrame после фильтрации"""
    return pd.DataFrame(
        {"Дата операции": ["01.11.2021 12:00:00"], "Категория": ["Супермаркеты"], "Сумма операции": [1000]}
    )


def mock_save_to_file(*args: Any, **kwargs: Any) -> Callable:
    """Mock-декоратор для подмены @save_to_file"""

    def wrapper(func: Callable) -> Callable:
        return func

    return wrapper


with patch("src.decorators.save_to_file", Mock(side_effect=mock_save_to_file)) as mock_decorator:
    from src.reports import expenses_by_days_of_the_week, get_report_by_category, expenses_by_working_day


def test_get_report_by_category_with_date(mock_data: pd.DataFrame) -> None:
    """Проверяем, что функция корректно работает с переданной датой и аргументами"""
    df = mock_data
    result = get_report_by_category(df, "Супермаркеты", "2021-12-31 23:59:59")
    expected_result = [{"Дата операции": "01.11.2021 12:00:00", "Категория": "Супермаркеты", "Сумма операции": -1000}]
    assert result == expected_result


def test_get_report_by_category_incorrect_date(mock_data: pd.DataFrame) -> None:
    """Проверяем, что при передаче некорректной даты вызывается исключение"""
    with pytest.raises(
        ValueError, match="Ошибка: передана некорректная дата! Используйте формат 'ГГГГ-ММ-ДД ЧЧ:ММ:СС'"
    ):
        get_report_by_category(mock_data, "Супермаркеты", "")


@patch("src.utils.get_date")
@freeze_time("2021-12-31 23:59:59")
def test_get_report_by_category_filters_by_date(mock_get_date: Mock) -> None:
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

    df = mock_data
    result = get_report_by_category(df, "Супермаркеты")
    parsed_result = result

    assert all(
        datetime.strptime(entry["Дата операции"], "%d.%m.%Y %H:%M:%S") >= datetime(2021, 10, 1, 0, 0, 0)
        for entry in parsed_result
    )


def test_logging_permission_error(caplog: LogCaptureFixture) -> None:
    with patch("os.makedirs"), patch("logging.FileHandler", side_effect=PermissionError("No permission")):
        from src.reports import loger

        loger.handlers.clear()
        with caplog.at_level(logging.ERROR, logger="reports"):
            from importlib import reload

            from src import reports

            reload(reports)
        assert "Ошибка доступа к файлу логов" in caplog.text


def test_expenses_by_days_of_the_week_succes(mock_data: pd.DataFrame) -> None:
    """Проверяем, что функция корректно работает с переданной датой и аргументами"""
    df = mock_data
    result = expenses_by_days_of_the_week(df, "2021-12-31 23:59:59")
    expected_result = pd.DataFrame(
        [
            {"День недели": "Monday", "Средние траты": 1000.0},
            {"День недели": "Tuesday", "Средние траты": np.nan},
            {"День недели": "Wednesday", "Средние траты": np.nan},
            {"День недели": "Thursday", "Средние траты": np.nan},
            {"День недели": "Friday", "Средние траты": 500.0},
            {"День недели": "Saturday", "Средние траты": np.nan},
            {"День недели": "Sunday", "Средние траты": np.nan},
        ]
    )
    result_df = pd.DataFrame(result)
    assert_frame_equal(result_df, expected_result, check_names=True)


def test_expenses_by_days_of_the_week_no_expenses(mock_data: pd.DataFrame) -> None:
    """
    Проверяем работу при отсутствии трат за период
    """
    mock_df = mock_data
    with pytest.raises(ValueError, match="Нет данных о расходах за указанный период"):
        expenses_by_days_of_the_week(mock_df, "2022-02-12 23:59:59")


def test_expenses_by_working_day_succes(mock_data: pd.DataFrame) -> None:
    """Проверяем, что функция корректно работает с переданной датой и аргументами"""
    df = mock_data
    result = expenses_by_working_day(df, "2021-12-31 23:59:59")
    expected_result = [{"Рабочие дни": 750, "Выходные": 0}]
    assert result == expected_result


def test_expenses_by_working_day_no_expenses(mock_data: pd.DataFrame) -> None:
    """
    Проверяем работу при отсутствии трат за период
    """
    mock_df = mock_data
    with pytest.raises(ValueError, match="Нет данных о расходах за указанный период"):
        expenses_by_days_of_the_week(mock_df, "2022-02-12 23:59:59")
