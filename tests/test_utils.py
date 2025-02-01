import re
from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.utils import filter_dataframe, get_data, greetings, get_date


@pytest.mark.parametrize(
    "mock_hour, expected_greeting",
    [
        (5, "Доброе утро!"),
        (10, "Доброе утро!"),
        (11, "Добрый день!"),
        (16, "Добрый день!"),
        (18, "Добрый вечер!"),
        (22, "Добрый вечер!"),
        (0, "Доброй ночи!"),
        (4, "Доброй ночи!"),
    ],
)
def test_greetings(mock_hour: Mock, expected_greeting: Mock) -> None:
    """Тест функции greetings для различных временных диапазонов."""
    # Создаем мок для datetime
    mock_datetime = Mock(wraps=datetime)
    mock_datetime.now.return_value = datetime(2025, 1, 25, mock_hour, 0, 0)

    # Патчим datetime в нужном модуле
    with patch("src.utils.datetime", mock_datetime):
        result = greetings()

        # Проверяем, что возвращается правильное приветствие
        assert result == expected_greeting, f"Ожидалось '{expected_greeting}', но получено '{result}'"


def test_get_data_success() -> None:
    """Тест успешного получения DataFrame из файла .xlsx."""
    # Создаем тестовый DataFrame
    test_data = {"Column1": [1, 2, 3], "Column2": ["A", "B", "C"]}
    test_df = pd.DataFrame(test_data)

    # Мокаем pd.read_excel, чтобы он возвращал наш тестовый DataFrame
    with patch("pandas.read_excel", return_value=test_df) as mock_read_excel:
        result = get_data("mock_path.xlsx")

        # Проверяем, что результат соответствует ожидаемому DataFrame
        pd.testing.assert_frame_equal(result, test_df)

        # Проверяем, что pd.read_excel был вызван с правильным аргументом
        mock_read_excel.assert_called_once_with("mock_path.xlsx")


def test_get_data_file_not_found() -> None:
    """Тест обработки ошибки FileNotFoundError."""
    # Мокаем pd.read_excel, чтобы он вызывал FileNotFoundError
    with patch("pandas.read_excel", side_effect=FileNotFoundError("Файл не найден")):
        with pytest.raises(FileNotFoundError, match="Файл не найден"):
            get_data("mock_path.xlsx")


def test_filter_dataframe_by_value() -> None:
    """Тест фильтрации по значениям"""
    df = pd.DataFrame({"Категории": ["Продукты", "Напитки", "Хлеб"], "Сумма": [1000, 2000, 1500]})
    coditions = {"Категории": "Напитки"}
    result = filter_dataframe(df, coditions)
    expected_result = pd.DataFrame({"Категории": ["Напитки"], "Сумма": [2000]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result)


def test_filter_dataframe_by_regex() -> None:
    """Тест фильтрации по регулярному выражению"""
    df = pd.DataFrame(
        {
            "Категории": ["Перевод", "Покупки", "Бонусы"],
            "Сумма": [1000, 2000, 1500],
            "Описание": ["Иванов А.", "Магазин", "Сидоров В."],
        }
    )
    coditions = {"Описание": re.compile(r"^\s*[А-ЯЁ]{1}[а-яё]+\s+[А-ЯЁ]{1}\.\s*$")}
    result = filter_dataframe(df, coditions)
    expected_result = pd.DataFrame(
        {"Категории": ["Перевод", "Бонусы"], "Сумма": [1000, 1500], "Описание": ["Иванов А.", "Сидоров В."]}
    )
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result)


def test_filter_dataframe_by_func() -> None:
    """Тест фильтрации с помощью функции"""
    df = pd.DataFrame(
        {
            "Категории": ["Перевод", "Покупки", "Бонусы"],
            "Сумма": [1000, 2000, 1500],
            "Описание": ["Иванов А.", "Магазин", "Сидоров В."],
        }
    )
    coditions = {"Сумма": (lambda x: x >= 2000)}
    result = filter_dataframe(df, coditions)
    expected_result = pd.DataFrame(
        {
            "Категории": [
                "Покупки",
            ],
            "Сумма": [2000],
            "Описание": ["Магазин"],
        }
    )
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result)


def test_filter_dataframe_with_and() -> None:
    """Тест фильтрации с использованием логического условия AND"""
    df = pd.DataFrame(
        {
            "Категории": ["Перевод", "Покупки", "Бонусы"],
            "Сумма": [1000, 2201, 1500],
            "Описание": ["Иванов А.", "Магазин", "Сидоров В."],
        }
    )
    coditions = {"Сумма": (lambda x: x >= 1000), "Категории": "Покупки"}
    result = filter_dataframe(df, coditions, "AND")
    expected_result = pd.DataFrame(
        {
            "Категории": [
                "Покупки",
            ],
            "Сумма": [2201],
            "Описание": ["Магазин"],
        }
    )
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result)


def test_filter_dataframe_with_or() -> None:
    """Тест фильтрации с использованием логического условия OR"""
    df = pd.DataFrame(
        {
            "Категории": ["Перевод", "Покупки", "Бонусы"],
            "Сумма": [1000, 2201, 1500],
            "Описание": ["Иванов А.", "Магазин", "Сидоров В."],
        }
    )
    coditions = {"Сумма": (lambda x: x >= 2500), "Категории": "Покупки"}
    result = filter_dataframe(df, coditions, "OR")
    expected_result = pd.DataFrame({"Категории": ["Покупки"], "Сумма": [2201], "Описание": ["Магазин"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result)


def test_filter_dataframe_combined_conditions() -> None:
    """Тест: комбинированные условия (функции, regex и значения)."""
    df = pd.DataFrame(
        {
            "Категории": ["Продукты", "Напитки", "Бонусы"],
            "Сумма": [1000, 2000, 3000],
            "Описание": ["Иванов А.", "Магазин", "Сидоров В."],
        }
    )
    conditions = {"Категории": "Напитки", "Сумма": lambda x: x > 1500, "Описание": re.compile(r"Магазин")}
    result = filter_dataframe(df, conditions, operator="AND")
    expected_result = pd.DataFrame({"Категории": ["Напитки"], "Сумма": [2000], "Описание": ["Магазин"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result)


def test_filter_dataframe_without_coditions() -> None:
    """Тест фильтрации с пустыми условиями"""
    df = pd.DataFrame(
        {
            "Категории": ["Перевод", "Покупки", "Бонусы"],
            "Сумма": [1000, 2201, 1500],
            "Описание": ["Иванов А.", "Магазин", "Сидоров В."],
        }
    )
    coditions: dict = {}
    result = filter_dataframe(df, coditions)
    expected_result = pd.DataFrame(
        {
            "Категории": ["Перевод", "Покупки", "Бонусы"],
            "Сумма": [1000, 2201, 1500],
            "Описание": ["Иванов А.", "Магазин", "Сидоров В."],
        }
    )
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result)


def test_invalid_operator() -> None:
    """Тест: исключение при некорректном операторе."""
    df = pd.DataFrame({"Категория": ["Переводы"], "Сумма": [1000]})
    conditions = {"Категория": "Переводы"}

    with pytest.raises(ValueError, match="Логический оператор должен быть строкой AND или OR"):
        filter_dataframe(df, conditions, operator="INVALID")


def test_filter_dataframe_empty_df() -> None:
    """Тест: пустой DataFrame должен вернуть пустой результат."""
    df = pd.DataFrame(columns=["Категории", "Сумма"])
    conditions = {"Категории": "Продукты"}
    result = filter_dataframe(df, conditions)
    expected_result = pd.DataFrame(columns=["Категории", "Сумма"])
    pd.testing.assert_frame_equal(result, expected_result)


def test_filter_dataframe_missing_column() -> None:
    """Тест: фильтрация по отсутствующему столбцу должна выбросить KeyError."""
    df = pd.DataFrame({"Категории": ["Продукты"], "Сумма": [1000]})
    conditions = {125: "Значение"}  # Несуществующий столбец
    with pytest.raises(KeyError, match="Столбцы \\[125\\] отсутствуют в DataFrame"):
        filter_dataframe(df, conditions)


@pytest.mark.parametrize(
    "mock_input, expected_output",
    [
        ("", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),  # Пустой ввод → текущая дата
        ("2021-12-31 23:59:59", "2021-12-31 23:59:59"),  # Корректная дата
    ],
)
@patch("builtins.input")  # Мокаем `input()`
def test_get_date(mock_input_function, mock_input, expected_output):
    """Тестируем разные сценарии работы get_date()."""

    mock_input_function.side_effect = [mock_input]  # Симулируем ввод пользователя
    result = get_date()  # Вызываем тестируемую функцию

    assert result == expected_output  # Проверяем корректность


@patch("builtins.input", side_effect=["invalid date", "2021-12-31 23:59:59"])  # 1-я попытка неверная, 2-я успешная
def test_get_date_invalid_retry(mock_input_function):
    """Тестируем сценарий, когда пользователь вводит некорректную дату и исправляет её."""

    result = get_date()
    assert result == "2021-12-31 23:59:59"



