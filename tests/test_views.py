from datetime import datetime

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.views import get_operations_for_current_month, sum_by_category, get_total_spending, get_top_5


@pytest.fixture
def sample_dataframe():
    """Фикстура для создания тестового DataFrame с транзакциями."""
    data = {
        "Дата операции": ["2025-01-10", "2025-01-20", "2025-02-05", "2025-01-25"],
        "Сумма": [100, 200, 300, 400],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    return df


def test_get_operations_current_month_default_date(sample_dataframe):
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


def test_get_operations_current_month_string_date(sample_dataframe):
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


def test_get_operations_current_month_datetime_date(sample_dataframe):
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


def test_get_operations_current_month_cutoff_date(sample_dataframe):
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


def test_get_operations_current_month_no_current_date(sample_dataframe):
    """Тест: передача аргумента current_date=None."""
    filtered_df = get_operations_for_current_month(sample_dataframe, None)
    # Проверяем, что фильтр отработал для текущего месяца (текущая дата - дата выполнения теста).
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    expected_df = sample_dataframe[
        (pd.to_datetime(sample_dataframe["Дата операции"]).dt.year == current_year) &
        (pd.to_datetime(sample_dataframe["Дата операции"]).dt.month == current_month)
        ]
    assert_frame_equal(filtered_df.reset_index(drop=True), expected_df.reset_index(drop=True))


def test_invalid_date_format(sample_dataframe):
    """Тест: передача некорректной даты (строка)."""
    with pytest.raises(ValueError, match="Передана некорректная дата: invalid-date"):
        get_operations_for_current_month(sample_dataframe, "invalid-date")


def test_invalid_date_type(sample_dataframe):
    """Тест: передача недопустимого типа данных в current_date."""
    with pytest.raises(ValueError, match="Аргумент .* должен быть строкой .* объектом datetime или None"):
        get_operations_for_current_month(sample_dataframe, 123)


def test_filter_empty_dataframe():
    """Тест: передача пустого DataFrame."""
    df = pd.DataFrame(columns=["Дата операции", "Сумма"])
    filtered_df = get_operations_for_current_month(df, "2025-01-27 00:00:00")
    assert filtered_df.empty


def test_sum_by_category_succes() -> None:
    """Тест успешной группировки по категориям"""
    data = {'Категория': ['первая', 'вторая', 'третья', 'первая'], 'Сумма операции с округлением': [100, 200, 300, 400]}
    df = pd.DataFrame(data)

    result = sum_by_category(df)
    expected_data = {'Категория': ['вторая', 'первая', 'третья'], 'Сумма операции с округлением': [200, 500, 300]}
    expected_result = pd.DataFrame(expected_data)
    assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))


def test_get_total_spending() -> None:
    """Тест успешной группировки по номерам карт"""
    data = {
        'Номер карты': ['1111', '2222', '4444', '2222'],
        'Сумма операции с округлением': [100, 200, 300, 400],
        "Кэшбэк": [1, 2, 4, 5]}
    df = pd.DataFrame(data)

    result = get_total_spending(df)
    expected_data = {'Номер карты': ['1111', '2222', '4444'],
                     'Сумма операции с округлением': [100, 600, 300],
                     "Кэшбэк": [1, 7, 4]}
    expected_result = pd.DataFrame(expected_data)
    assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))


def test_get_top_5() -> None:
    """Тест фильтрации Топ-5 транзакций"""
    data = {
        "Дата операции": ['2021-25-06', '2021-24-06', '2021-20-06', '2020-25-06', '2018-25-06', '2020-25-08', '2019-25-08'],
        "Сумма операции с округлением": [1600, 16000, 20, 50, 100, 1000, 47],
        "Категория": ['1', '2', '3', '4', '5', '6', '7'],
        "Описание": ['Колхоз', 'Ozon.ru', 'Константин Л.', 'Константин Л.', 'Ситидрайв', 'РЖД', 'Mouse Tail'
                     ]}
    df = pd.DataFrame(data)
    result = get_top_5(df)

    expected_data = {
        "Дата операции": ['2021-24-06', '2021-25-06', '2020-25-08', '2018-25-06', '2020-25-06'],
        "Сумма операции с округлением": [16000, 1600, 1000, 100, 50],
        "Категория": ['2', '1', '6', '5', '4'],
        "Описание": ['Ozon.ru', 'Колхоз', 'РЖД', 'Ситидрайв', 'Константин Л.'
                     ]}
    expected_result = pd.DataFrame(expected_data)
    assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))