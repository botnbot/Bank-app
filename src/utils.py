import re
from datetime import datetime
from typing import Any, Optional

import pandas as pd
from pandas import DataFrame, Timestamp


def greetings() -> str:
    """
    Функция возвращает приветствие в зависимости от времени суток
    """
    time = datetime.now().hour
    if 4 < time <= 10:
        return "Доброе утро!"
    elif 10 < time <= 17:
        return "Добрый день!"
    elif 17 < time <= 23:
        return "Добрый вечер!"
    else:
        return "Доброй ночи!"


def get_data(path: str = r"C:\Projects\Bank_app\data\operations.xlsx") -> pd.DataFrame:
    """
    Функция принимает на вход путь к файлу .xlsx в виде строки и возвращает DataFrame с транзакциями
         Args:
             path(str): путь к файлу
        Returns:
            Optional[pd.DataFrame]: DataFrame, если файл найден, иначе None.
    """
    try:
        return pd.read_excel(path)
    except FileNotFoundError:
        raise FileNotFoundError("Файл не найден. Проверьте наличие файла и перезапустите программу")


def filter_dataframe(df: pd.DataFrame, filtr_conditions: dict, operator: str = "AND") -> Any:
    """
    Функция принимает DataFrame с транзакциями, и фильтрует его по заданным условиям.
    Args:
        df: - Исходный DataFrame
        filtr_conditions: - Условия, по которым нужно фильтровать DataFrame
        operator: - Логический оператор, который объединяет условия фильтрации ("AND", "OR")
    Returns:
        Отфильтрованый DataFrame
    """

    if operator not in ("AND", "OR"):
        raise ValueError("Логический оператор должен быть строкой AND или OR")

    if not filtr_conditions:
        return df

    # Проверяем, что все ключи есть в столбцах DataFrame
    missing_keys = [key for key in filtr_conditions if key not in df.columns]
    if missing_keys:
        raise KeyError(f"Столбцы {missing_keys} отсутствуют в DataFrame")

    conditions = []
    for key, condition in filtr_conditions.items():
        if callable(condition):
            # Если передана функция, применяем её
            conditions.append(condition(df[key]))
        elif isinstance(condition, re.Pattern):
            # Если передано регулярное выражение, применяем его
            conditions.append(df[key].apply(lambda x: bool(condition.match(str(x)))))
        else:
            # Если передано значение, проверяем равенство
            conditions.append(df[key] == condition)

    combined_conditions = conditions[0]
    for condition in conditions[1:]:
        if operator == "AND":
            combined_conditions &= condition
        else:
            combined_conditions |= condition

    filtered_df = df[combined_conditions]
    return filtered_df


def get_date() -> str:
    """
    Функция, запрашивающая у пользователя дату для передачи в функцию.
    Возвращает дату в формате "YYYY-MM-DD HH:MM:SS".
    Если ввод пустой, возвращает текущую дату.
    """
    while True:
        try:
            date_input: str = input(
                "Введите строку с датой и временем в формате YYYY-MM-DD HH:MM:SS "
                "в диапазоне с 2018-01-01 по 2021-12-31, "
                "или нажмите Enter для использования текущей даты:\n"
            ).strip()

            if not date_input:
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            date = datetime.strptime(date_input, "%Y-%m-%d %H:%M:%S")
            return date.strftime("%Y-%m-%d %H:%M:%S")

        except ValueError as e:
            print(f"Не удалось получить дату: {e}. Попробуйте снова.")


def get_df_for_current_period(date: str, df: Optional[pd.DataFrame], period_type: str = "M") -> Any:
    """
    Возвращает транзакции за заданный период.
    Функция принимает DataFrame со всеми транзакциями и фильтрует его, оставляя только операции,
    которые произошли в пределах заданного периода.
    Args:
        df (DataFrame): Исходный DataFrame с транзакциями. Должен содержать столбец "Дата операции".
        date (str): Строка с датой и временем в формате YYYY-MM-DD HH:MM:SS для определения заданного периода.
        Если не передана, используется текущая дата.
        period_type (str): Диапазон данных. По умолчанию диапазон равен одному месяцу
         (с начала месяца, на который выпадает дата, по саму дату).
         Возможные значения параметра:
         W — неделя, на которую приходится дата;
         M — месяц, на который приходится дата;
         Y — год, на который приходится дата;
         ALL — все данные до указанной даты.
    Returns:
        DataFrame: Отфильтрованный DataFrame с транзакциями за текущий период.
    """
    if df is None:
        raise ValueError("Ошибка: передан пустой DataFrame (None).")
    # Преобразуем дату в datetime
    parsed_date = pd.to_datetime(date, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    if pd.isna(parsed_date):
        raise ValueError("Ошибка: передана некорректная дата! Запустите с корректными параметрами.")

    df = df.copy()

    if "Дата операции" not in df.columns:
        raise ValueError('Ошибка: в DataFrame отсутствует столбец "Дата операции".')

    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce", dayfirst=True)
    df.dropna(subset=["Дата операции"], inplace=True)

    current_week = parsed_date.isocalendar().week
    current_month = parsed_date.month
    current_year = parsed_date.year

    period_filters = {
        "W": lambda dates: (dates <= parsed_date)
        & (dates.dt.year == current_year)
        & (dates.dt.isocalendar().week == current_week),
        "M": lambda dates: (dates <= parsed_date)
        & (dates.dt.year == current_year)
        & (dates.dt.month == current_month),
        "Y": lambda dates: (dates <= parsed_date) & (dates.dt.year == current_year),
        "ALL": lambda dates: (dates <= parsed_date),
    }

    if period_type not in period_filters:
        raise ValueError("Ошибка: передан некорректный период. Допустимые значения: W, M, Y, ALL.")

    current_period_df = df[period_filters[period_type](df["Дата операции"])]

    if "Номер карты" in current_period_df.columns:
        current_period_df.loc[:, "Номер карты"] = current_period_df["Номер карты"].astype(str).str[-4:]

    return current_period_df


def extract_mobile_numbers(text: str) -> list[str]:
    """
    Извлекает из строки все подстроки, которые начинаются с +7 или 8, содержат разделители (пробелы, скобки, дефисы)
     и, после удаления нецифровых символов, имеют ровно 11 цифр.
    Args:
        text(str) - подстрока для поиска
    Returns:
        list[str] - список извлеченных подстрок
    """
    # Ищем потенциальные кандидаты: начинаются с +7 или 8 и содержат цифры, пробелы, скобки, дефисы.
    pattern = re.compile(r"(?:\+7|8)[\d\s()-]+")
    candidates = pattern.findall(text)

    valid_numbers = []
    for cand in candidates:
        # Удаляем все символы, не являющиеся цифрами.
        digits = re.sub(r"\D", "", cand)
        # Если после удаления остаётся ровно 11 цифр, то номер валиден.
        if len(digits) == 11:
            valid_numbers.append(cand.strip())
    return valid_numbers


def get_3_months_data(df: DataFrame, date: Any = None) -> DataFrame:
    """
    Фильтрует DataFrame, оставляя данные только за 3 месяца от указанной даты.

    Args:
        df (DataFrame): DataFrame с транзакциями (должен содержать 'Дата операции')
        date (str, optional): Дата в формате 'ГГГГ-ММ-ДД ЧЧ:ММ:СС' (например '2023-12-31 23:59:59')

    Returns:
        DataFrame: Отфильтрованный DataFrame с данными за последние 3 месяца

    Raises:
        ValueError: Если передан некорректный формат даты или отсутствует нужный столбец
    """

    if "Дата операции" not in df.columns:
        raise ValueError('Ошибка: В DataFrame отсутствует столбец "Дата операции"')

    if date is None:
        stop_date: Timestamp = pd.Timestamp.now()
    else:
        temp_date = pd.to_datetime(date, format="%Y-%m-%d %H:%M:%S", errors="coerce")
        if pd.isna(temp_date):
            raise ValueError("Ошибка: передана некорректная дата! Используйте формат 'ГГГГ-ММ-ДД ЧЧ:ММ:СС'")
        stop_date = Timestamp(temp_date)

    # Вычисляем дату 3 месяца назад
    start_date = stop_date - pd.DateOffset(months=3)
    df = df.copy()
    df["Дата операции временная"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")
    if df["Дата операции временная"].isna().all():
        raise ValueError("Ошибка: Все даты в DataFrame оказались некорректными!")

    # Фильтруем транзакции за последние 3 месяца
    filtered_df = df.dropna(subset=["Дата операции временная"])
    filtered_df = filtered_df[
        (filtered_df["Дата операции временная"] >= start_date) & (filtered_df["Дата операции временная"] <= stop_date)
    ]

    return filtered_df.drop(columns=["Дата операции временная"])
