import json
import os
import time
from functools import wraps
from typing import Any, Callable

from config import ROOT_PATH


def save_to_file(file_name: Any = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Декоратор, который записывает в файл результат, возвращаемый функцией, в формате JSON.
    Имя файла состоит из имени модуля, где определена декорируемая функция, и времени создания файла.
    """

    def generate_file_name(func: Callable[..., Any]) -> str:
        """
        Генерирует имя файла на основе модуля, где определена декорируемая функция, и текущего времени.
        """
        # Получаем путь к исходному файлу, где функция была определена
        func_file_path = func.__code__.co_filename

        # Определяем имя модуля из пути к файлу
        module_name = os.path.splitext(os.path.basename(func_file_path))[0]

        # Генерируем имя файла с временной меткой
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        return os.path.join(ROOT_PATH, "data", "output", f"{module_name}_{timestamp}.json")

    def inner(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal file_name
            if file_name is not None and not isinstance(file_name, str):
                raise TypeError(f"Имя файла должно быть строкой, получено: {type(file_name).__name__}")

            # Генерируем имя файла, если имя не передано
            final_file_name = file_name or generate_file_name(func)
            final_file_name = os.path.normpath(final_file_name)

            if not os.path.isabs(final_file_name):
                final_file_name = os.path.join(ROOT_PATH, final_file_name)

            if os.path.isdir(final_file_name):
                raise ValueError("Указанный путь является директорией, ожидался файл.")

            try:
                os.makedirs(os.path.dirname(final_file_name), exist_ok=True)
                result = func(*args, **kwargs)

                # Запись результата в файл в формате JSON
                with open(final_file_name, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False)
                return result

            except Exception:
                raise

        return wrapper

    return inner
