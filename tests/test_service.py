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

from config import ROOT_PATH


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

    mock_log_info.assert_any_call("Данные из файла загружены")


def test_logging_permission_error(caplog: LogCaptureFixture) -> None:
    with patch("os.makedirs"), patch("logging.FileHandler", side_effect=PermissionError("No permission")):
        from src.services import loger

        loger.handlers.clear()
        with caplog.at_level(logging.ERROR, logger="services"):
            from importlib import reload

            from src import services

            reload(services)
        assert "Ошибка доступа к файлу логов" in caplog.text
