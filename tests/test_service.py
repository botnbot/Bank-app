import re
from collections.abc import Callable
from typing import Any
from unittest.mock import Mock, patch

import pandas as pd
import pytest


# Замокаем декоратор до импорта функции
def mock_save_to_file(*args: Any, **kwargs: Any) -> Callable:
    def wrapper(func: Callable) -> Callable:
        return func

    return wrapper


with patch("src.decorators.save_to_file", Mock(side_effect=mock_save_to_file)) as mock_decorator:
    from src.services import find_money_transfers_from_individuals


def test_find_money_transfers_file_not_found() -> None:
    """Тест для случая, когда путь к файлу некорректен."""
    with patch("src.services.get_data") as mock_get_data:  # Мок функции get_data
        # Мокаем исключение при попытке загрузить файл
        mock_get_data.side_effect = FileNotFoundError("Файл не найден")

        # Проверяем, что возникает исключение
        with pytest.raises(FileNotFoundError, match="Файл не найден"):
            find_money_transfers_from_individuals("invalid_path")

        # Проверяем, что get_data был вызван с правильным аргументом
        print("Вызовы mock_get_data:", mock_get_data.call_args_list)  # Для отладки
        mock_get_data.assert_called_once_with("invalid_path")


@patch("src.services.get_data")  # Используем путь, по которому вызывается get_data
@patch("src.services.filter_dataframe")  # Проверяем filter_dataframe
def test_find_money_transfers_valid(mock_filter_dataframe: Mock, mock_get_data: Mock) -> None:
    """Тест для валидных данных."""

    # Подготовка тестового DataFrame
    mock_df = pd.DataFrame(
        {
            "Категория": ["Переводы", "Переводы", "Покупки"],
            "Описание": ["Иванов И.", "Петров П.", "Магазин"],
            "Сумма": [1000, 2000, 500],
        }
    )
    mock_get_data.return_value = mock_df  # Устанавливаем возвращаемое значение get_data

    # Подготовка результата фильтрации
    filtered_df = pd.DataFrame(
        {"Категория": ["Переводы", "Переводы"], "Описание": ["Иванов И.", "Петров П."], "Сумма": [1000, 2000]}
    )
    mock_filter_dataframe.return_value = filtered_df  # Мокаем результат filter_dataframe

    # Вызов тестируемой функции
    result = find_money_transfers_from_individuals("mock_path")

    # Ожидаемый результат
    expected_result = (
        '[{"Категория":"Переводы","Описание":"Иванов И.","Сумма":1000},'
        '{"Категория":"Переводы","Описание":"Петров П.","Сумма":2000}]'
    )

    # Проверяем результат
    assert result == expected_result

    # Проверяем, что функции были вызваны с правильными аргументами
    mock_get_data.assert_called_once_with("mock_path")
    mock_filter_dataframe.assert_called_once_with(
        mock_df,
        {"Категория": "Переводы", "Описание": re.compile(r"^\s*[A-ZА-ЯЁ]{1}[a-zа-яё]+\s+[A-ZА-ЯЁ]{1}\.\s*$")},
        "AND",
    )


@patch("src.services.get_data")
@patch("src.services.filter_dataframe")
def test_find_money_transfers_no_data(mock_filter_dataframe: Mock, mock_get_data: Mock) -> None:
    """Test when there are no matching transfers."""

    # Мокаем входные данные
    mock_df = pd.DataFrame(
        {"Категория": ["Покупки", "Покупки"], "Описание": ["Магазин", "Ресторан"], "Сумма": [500, 1000]}
    )
    mock_get_data.return_value = mock_df

    # Мокаем результат фильтрации (пустой DataFrame)
    filtered_df = pd.DataFrame(columns=["Категория", "Описание", "Сумма"])
    mock_filter_dataframe.return_value = filtered_df

    # Вызываем функцию
    result = find_money_transfers_from_individuals("mock_path")

    # Ожидаемый результат
    expected_result = "[]"

    # Проверка результата
    assert result == expected_result

    # Проверяем вызовы зависимостей
    mock_get_data.assert_called_once_with("mock_path")
    mock_filter_dataframe.assert_called_once()
