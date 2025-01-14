import os.path
import re

from pandas import DataFrame

from src.decorators import save_to_file
from src.utils import filter_dataframe, get_data
from config import ROOT_PATH
module_name = 'services'
@save_to_file()
def find_money_transfers_from_individuals(data_path: str) -> DataFrame:
    """Функция, возвращающая DataFrame с переводами только физическим лицам.
     Args:
        data_path (str): путь к исходному DataFrame.
    Returns:
        DataFrame: Отфильтрованный DataFrame."""
    pattern = re.compile(r"^\s*[A-ZА-ЯЁ]{1}[a-zа-яё]+\s+[A-ZА-ЯЁ]{1}\.\s*$")
    df = get_data(data_path)
    filter_conditions = {"Категория": "Переводы", "Описание": pattern}
    result = filter_dataframe(df, filter_conditions, "AND")
    return result.to_json(orient= 'records', force_ascii=False)


if __name__ == "__main__":
    data_path = os.path.join(ROOT_PATH, 'data', 'operations.xlsx')
    transfers_from_individuals = find_money_transfers_from_individuals(data_path)
    print(transfers_from_individuals)
