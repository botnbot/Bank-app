import os.path
import re
from typing import Optional

from pandas import DataFrame

from src.decorators import save_to_file
from src.utils import filter_dataframe, get_data
from config import ROOT_PATH

@save_to_file()
def find_money_transfers_from_individuals(data_path: str) -> str:
    """Функция, возвращающая DataFrame с переводами только физическим лицам.
     Args:
        data_path (str): путь к исходному DataFrame.
    Returns:
        DataFrame: Отфильтрованный DataFrame."""
    pattern = re.compile(r"^\s*[A-ZА-ЯЁ]{1}[a-zа-яё]+\s+[A-ZА-ЯЁ]{1}\.\s*$")
    df = get_data(data_path)
    filter_conditions = {"Категория": "Переводы", "Описание": pattern}
    result = filter_dataframe(df, filter_conditions, "AND")
    return result.to_json(orient='records', force_ascii=False)


if __name__ == "__main__":
    while True:
        try:
            date: Optional[str] = input(
                "Введите строку с датой и временем в формате YYYY-MM-DD HH:MM:SS"
                " в диапазоне с 2018-01-01 по 2021-12-31,"
                " или нажмите Enter для использования текущей даты: "
            ).strip()
            if not date:  # Пустой ввод — текущая дата
                date = None
            path = os.path.join(ROOT_PATH, 'data', 'operations.xlsx')
            print(find_money_transfers_from_individuals(path))
            break
        except ValueError as e:
            print(e)

