import json
import logging
import os
import re
from collections.abc import Callable
from typing import Any, Generator
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from _pytest.logging import LogCaptureFixture
from pandas import DataFrame

from config import ROOT_PATH
from src.services import investment_bank, profitable_cashback, simple_search


@pytest.fixture(scope="function", autouse=True)
def disable_logging() -> Generator:
    """Отключает логирование на время тестов."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


# мокаем декоратор
def mock_save_to_file(*args: Any, **kwargs: Any) -> Callable:
    """Mock-декоратор для подмены @save_to_file"""

    def wrapper(func: Callable) -> Callable:
        return func

    return wrapper


with patch("src.decorators.save_to_file", Mock(side_effect=mock_save_to_file)) as mock_decorator:
    from src.services import find_money_transfers_from_individuals


@patch("src.services.get_data")
@patch("src.services.filter_dataframe")
@patch("os.path.exists", return_value=True)
def test_find_money_transfers_valid(mock_exists: Mock, mock_filter_dataframe: Mock, mock_get_data: Mock) -> None:
    """Тест проверяет, что находятся корректные переводы от физических лиц."""

    expected_path = os.path.join(ROOT_PATH, "test_data.csv")

    mock_df = pd.DataFrame(
        {
            "Категория": ["Переводы", "Переводы", "Покупки"],
            "Описание": ["Иванов И.", "Петров П.", "Магазин"],
            "Сумма": [1000, 2000, 500],
        }
    )
    mock_get_data.return_value = mock_df

    filtered_df = mock_df[mock_df["Категория"] == "Переводы"]
    mock_filter_dataframe.return_value = filtered_df

    result = find_money_transfers_from_individuals("test_data.csv")

    expected_result = json.dumps(
        [
            {"Категория": "Переводы", "Описание": "Иванов И.", "Сумма": 1000},
            {"Категория": "Переводы", "Описание": "Петров П.", "Сумма": 2000},
        ],
        ensure_ascii=False,
    )

    assert json.loads(result) == json.loads(expected_result)
    mock_get_data.assert_called_once_with(expected_path)
    mock_filter_dataframe.assert_called_once_with(
        mock_df,
        {"Категория": "Переводы", "Описание": re.compile(r"^\s*[A-ZА-ЯЁ]{1}[a-zа-яё]+\s+[A-ZА-ЯЁ]{1}\.\s*$")},
        "AND",
    )


@patch("src.services.get_data")
@patch("src.services.filter_dataframe")
@patch("os.path.exists", return_value=True)
def test_find_money_transfers_no_data(mock_exists: Mock, mock_filter_dataframe: Mock, mock_get_data: Mock) -> None:
    """Тест, когда в возвращаемом ответе пусто"""

    expected_path = os.path.join(ROOT_PATH, "test_data.csv")
    mock_df = pd.DataFrame(
        {"Категория": ["Покупки", "Покупки"], "Описание": ["Магазин", "Ресторан"], "Сумма": [500, 1000]}
    )
    mock_get_data.return_value = mock_df
    filtered_df = pd.DataFrame(columns=["Категория", "Описание", "Сумма"])
    mock_filter_dataframe.return_value = filtered_df

    result = find_money_transfers_from_individuals("test_data.csv")
    expected_result = "[]"
    assert result == expected_result

    mock_get_data.assert_called_once_with(expected_path)
    mock_filter_dataframe.assert_called_once()


@patch("src.services.get_data", side_effect=FileNotFoundError("Файл с данными не найден"))
@patch("src.services.loger.error")
def test_log_error_when_file_not_found(mock_log_error: Mock, mock_get_data: Mock) -> None:
    """Тестирует логирование ошибки, когда файл не найден."""

    with pytest.raises(FileNotFoundError, match="Файл с данными не найден"):
        find_money_transfers_from_individuals("test_data.csv")
    mock_log_error.assert_called_with("Ошибка доступа к файлу с данными: Файл с данными не найден")


@patch("src.services.get_data", return_value=pd.DataFrame({"Категория": ["Переводы"], "Описание": ["Иванов И."]}))
@patch("src.services.loger.info")
def test_log_info_when_file_loaded(mock_log_info: Mock, mock_get_data: Mock) -> None:
    """Тестирует логирование успешной загрузки файла."""

    find_money_transfers_from_individuals("test_data.csv")

    assert any("Успешная загрузка из файла" in call.args[0] for call in mock_log_info.call_args_list)


def test_logging_permission_error(caplog: LogCaptureFixture) -> None:
    with patch("os.makedirs"), patch("logging.FileHandler", side_effect=PermissionError("No permission")):
        from src.services import loger

        loger.handlers.clear()
        with caplog.at_level(logging.ERROR, logger="services"):
            from importlib import reload

            from src import services

            reload(services)
        assert "Ошибка доступа к файлу логов" in caplog.text


def test_profitable_cashback_sucsess() -> None:
    """Успешный тест с корректными данными"""
    mock_df = pd.DataFrame(
        {
            "Дата операции": ["22.08.2018 22:59:48", "22.12.2021 01:01:01", "04.12.2021 07:15:48"],
            "Категория": ["Дом и ремонт", "Супермаркеты", "Фастфуд"],
            "Кэшбэк": [5, 15, 10],
        }
    )
    result = profitable_cashback(mock_df, 2021, 12)
    expected_result = '{\n  "Супермаркеты":15,\n  "Фастфуд":10\n}'

    assert result == expected_result, f"Expected:\n{expected_result}\n but got:\n{result}"


def test_profitable_cashback_incorrect_month(caplog: LogCaptureFixture) -> None:
    """Тест логирования ошибки при некорректном месяце"""
    mock_df = pd.DataFrame({"Дата операции": ["04.12.2021 07:15:48"]})

    with caplog.at_level(logging.ERROR):
        profitable_cashback(mock_df, 2021, 15)

    log_messages = [record.message for record in caplog.records]

    assert "Передана некорректная дата" in log_messages, "Ожидаемая ошибка не была залогирована"
    caplog.clear()


@pytest.fixture
def sample_data() -> DataFrame:
    return pd.DataFrame(
        {
            "Описание": ["Кофе Starbucks", "Оплата за интернет", "Покупка в Магните"],
            "Категория": ["Еда", "Интернет", "Супермаркет"],
            "Сумма": [300, 500, 1500],
        }
    )


def test_successful_search(sample_data: Mock) -> None:
    with patch("src.services.get_data", return_value=sample_data):
        result = simple_search("кофе")
        result_data = json.loads(result)
        assert len(result_data) == 1
        assert result_data[0]["Описание"] == "Кофе Starbucks"


def test_empty_result(sample_data: Mock) -> None:
    with patch("src.services.get_data", return_value=sample_data):
        result = simple_search("несуществующий запрос")
        assert json.loads(result) == {"Итог": "Ничего не найдено."}


def test_case_insensitive(sample_data: Mock) -> None:
    with patch("src.services.get_data", return_value=sample_data):
        result_lower = simple_search("магнит")
        result_upper = simple_search("МАГНИТ")
        assert json.loads(result_lower) == json.loads(result_upper)


def test_category_search(sample_data: Mock) -> None:
    with patch("src.services.get_data", return_value=sample_data):
        result = simple_search("еда")
        result_data = json.loads(result)
        assert result_data[0]["Категория"] == "Еда"


def test_logging(sample_data: Mock, caplog: pytest.LogCaptureFixture) -> None:
    with patch("src.services.get_data", return_value=sample_data):
        with caplog.at_level(logging.INFO):
            simple_search("тест")
            assert "Поиск выполнен по запросу: 'тест'" in caplog.text


@pytest.fixture
def mock_transactions() -> list:
    return [
        {"Дата операции": "2018-01", "Сумма операции": 124},
        {"Дата операции": "2018-04", "Сумма операции": 567},
        {"Дата операции": "2019-01", "Сумма операции": 890},
        {"Дата операции": "2018-04", "Сумма операции": 123},
    ]


@pytest.fixture
def mock_transactions_with_mising_date() -> list:
    return [
        {"Дата операции": "NaT", "Сумма операции": 567},
        {"Дата операции": "", "Сумма операции": 537},
        {"Дата операции": "2019-01", "Сумма операции": 890},
        {"Дата операции": "2018-04", "Сумма операции": 123},
    ]


def test_investment_bank_correct_data(mock_transactions: Mock) -> None:
    """Успешный тест с корректными аргументами"""
    result = investment_bank("2018-04", mock_transactions, 50)
    expected_result = 60
    assert result == expected_result


def test_investment_bank_incorrect_date(mock_transactions: Mock) -> None:
    """Тест передачи некорректной даты в качестве аргумента"""
    with pytest.raises(ValueError):
        investment_bank("2018-14", mock_transactions, 50)


def test_investment_bank_missing_date_in_dataframe(mock_transactions_with_mising_date: Mock) -> None:
    """Тест передачи DataFrame с пропущенными датами в качестве аргумента"""
    result = investment_bank("2018-04", mock_transactions_with_mising_date, 50)
    expected_result = 27
    assert result == expected_result
