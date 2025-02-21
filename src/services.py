import logging
import os.path
import re
from logging import DEBUG, Formatter, getLogger
from typing import Any

from config import ROOT_PATH
from src.decorators import save_to_file
from src.utils import filter_dataframe, get_data

loger = getLogger("services")
formatter = Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
loger.setLevel(DEBUG)

consolehandler = logging.StreamHandler()
consolehandler.setFormatter(formatter)
consolehandler.setLevel(DEBUG)

logpath = os.path.join(ROOT_PATH, "logs")
os.makedirs(logpath, exist_ok=True)
logfile = os.path.join(ROOT_PATH, "logs", "log.txt")

try:
    filehandler = logging.FileHandler(logfile, mode="a")
    filehandler.setFormatter(formatter)
    filehandler.setLevel(logging.WARNING)
    if not loger.handlers:
        loger.addHandler(consolehandler)
        loger.addHandler(filehandler)
except PermissionError as e:
    loger.error(f"Ошибка доступа к файлу логов: {e}")


@save_to_file()
def find_money_transfers_from_individuals(data_path: str) -> Any:
    """
    Функция, возвращающая JSON с переводами только физическим лицам.
     Args:
        data_path (str): путь к исходному DataFrame.
    Returns:
        str: Отфильтрованный JSON
    """

    try:
        full_data_path = os.path.join(ROOT_PATH, data_path)
        df = get_data(full_data_path)
        loger.info("Данные из файла загружены")
    except FileNotFoundError as e:
        loger.error(f"Ошибка доступа к файлу с данными: {e}")
        raise FileNotFoundError("Файл с данными не найден")

    pattern = re.compile(r"^\s*[A-ZА-ЯЁ]{1}[a-zа-яё]+\s+[A-ZА-ЯЁ]{1}\.\s*$")
    filter_conditions = {"Категория": "Переводы", "Описание": pattern}
    result = filter_dataframe(df, filter_conditions, "AND")
    loger.info("Ответ сформирован")
    return result.to_json(orient="records", force_ascii=False)


if __name__ == "__main__":
    print(find_money_transfers_from_individuals("data/operations.xlsx"))
