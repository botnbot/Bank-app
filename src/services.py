import logging
import os.path
import re
from logging import getLogger, Formatter, DEBUG, WARNING
from typing import Optional, Any, Union

from config import ROOT_PATH
from src.decorators import save_to_file
from src.utils import filter_dataframe, get_data





@save_to_file()
def find_money_transfers_from_individuals() -> Union[str, Any]:
    """Функция, возвращающая JSON с переводами только физическим лицам.
     Args:
        data_path (str): путь к исходному DataFrame.
    Returns:
        str: Отфильтрованный JSON."""

    loger = getLogger('reports')
    formatter = Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    loger.setLevel(DEBUG)

    consolehandler = logging.StreamHandler()
    consolehandler.setFormatter(formatter)
    consolehandler.setLevel(DEBUG)

    logpath = os.path.join(ROOT_PATH, 'logs')
    os.makedirs(logpath, exist_ok=True)
    logfile = os.path.join(ROOT_PATH, 'logs', 'log.txt')

    try:
        filehandler = logging.FileHandler(logfile, mode="a")
        filehandler.setFormatter(formatter)
        filehandler.setLevel(WARNING)
        if not loger.handlers:
            loger.addHandler(consolehandler)
            loger.addHandler(filehandler)
    except PermissionError as e:
        loger.error(f"Ошибка доступа к файлу логов: {e}")


    pattern = re.compile(r"^\s*[A-ZА-ЯЁ]{1}[a-zа-яё]+\s+[A-ZА-ЯЁ]{1}\.\s*$")
    try:
        data_path = os.path.join(ROOT_PATH, 'data', 'operations.xlsx')
        df = get_data(data_path)
        loger.debug("Данные из файла загружены")
    except FileNotFoundError as e:
        loger.error(f"Ошибка доступа к файлу с данными: {e}")
        raise FileNotFoundError("Файл не с данными найден")


    filter_conditions = {"Категория": "Переводы", "Описание": pattern}
    result = filter_dataframe(df, filter_conditions, "AND")
    loger.info("Ответ сформирован")
    return result.to_json(orient="records", force_ascii=False)


if __name__ == "__main__":
    print(find_money_transfers_from_individuals())

#     while True:
#         try:
#             date: Optional[str] = input(
#                 "Введите строку с датой и временем в формате YYYY-MM-DD HH:MM:SS"
#                 " в диапазоне с 2018-01-01 по 2021-12-31,"
#                 " или нажмите Enter для использования текущей даты: "
#             ).strip()
#             if not date:  # Пустой ввод — текущая дата
#                 date = None
#             path = os.path.join(ROOT_PATH, "data", "operations.xlsx")
#             print(find_money_transfers_from_individuals(path))
#             break
#         except ValueError as e:
#             print(e)
