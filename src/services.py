import re
from typing import Any

from src.decorators import save_to_file
from src.utils import filter_dataframe, get_data


@save_to_file()
def find_money_transfers_from_individuals(data_path: str) -> Any:
    """Функция, возвращающая JSON с переводами только физическим лицам.
     Args:
        data_path (str): путь к исходному DataFrame.
    Returns:
        str: Отфильтрованный JSON."""
    pattern = re.compile(r"^\s*[A-ZА-ЯЁ]{1}[a-zа-яё]+\s+[A-ZА-ЯЁ]{1}\.\s*$")
    try:
        df = get_data(data_path)
    except FileNotFoundError:
        raise FileNotFoundError("Файл не найден")

    filter_conditions = {"Категория": "Переводы", "Описание": pattern}
    result = filter_dataframe(df, filter_conditions, "AND")
    return result.to_json(orient="records", force_ascii=False)
