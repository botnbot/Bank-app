import inspect
import os
import time
from functools import wraps
from typing import Any, Callable, Optional

from config import ROOT_PATH


def save_to_file(file_name: Optional[str] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Декоратор, который записывает в файл результат, возвращаемый функцией.
    Файл находится по пути data/output/, имя файла состоит из названия модуля,
    в котором находится декорируемая функция, и времени создания файла.
    """

    def generate_file_name(func: Callable[..., Any]) -> str:
        """Генерирует имя файла на основе имени модуля и текущего времени."""
        module = inspect.getmodule(func)
        module_name = (
            module.__name__
            if module and module.__name__ not in {"__main__", "<frozen runpy>", ""}
            else os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0]
        )

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        return os.path.join(ROOT_PATH, "data", "output", f"{module_name}_{timestamp}.json")

    def inner(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal file_name
            if file_name is not None and not isinstance(file_name, str):
                raise TypeError(f"Имя файла должно быть строкой, получено: {type(file_name).__name__}")

            final_file_name = file_name or generate_file_name(func)
            final_file_name = os.path.normpath(final_file_name)
            if not os.path.isabs(final_file_name):
                final_file_name = os.path.join(ROOT_PATH, final_file_name)

            if os.path.isdir(final_file_name):
                raise ValueError("Указанный путь является директорией, ожидался файл.")

            try:
                os.makedirs(os.path.dirname(final_file_name), exist_ok=True)
                result = func(*args, **kwargs)

                # Запись результата в файл
                with open(final_file_name, "w", encoding="utf-8") as f:
                    f.write(str(result))
                return result

            except Exception as e:
                raise RuntimeError(f"Ошибка в функции или при сохранении файла: {e}")

        return wrapper

    return inner
