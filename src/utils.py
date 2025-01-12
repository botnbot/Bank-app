from datetime import datetime
import pandas as pd


def greetings() -> str:
    """Функция возвращает приветствие в зависимости от времени суток"""
    time = datetime.now().hour
    if 4 < time <= 10:
        return 'Доброе утро!'
    elif 10 < time <= 17:
        return 'Добрый день!'
    elif 17 < time <= 23:
        return 'Добрый вечер!'
    else:
        return 'Доброй ночи!'


def get_data(path: str) -> pd.DataFrame:
    """Функция принимает на вход путь к файлу .xlsx и возвращает DataFrame"""
    df = pd.read_excel(path)
    return df


if __name__ == '__main__':
    print(get_data('data/operations.xlsx').head())
    print(get_data('data/operations.xlsx').shape)
    print(greetings())
