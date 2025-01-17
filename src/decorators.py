import inspect
import os
import time
from functools import wraps
from typing import Any, Callable, Optional

from config import ROOT_PATH


def save_to_file(file_name: Optional[str] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Декоратор, который записывает в файл результат, возвращаемый функцией.
    Файл находится по пути data/output/, имя файла состоит из названия модуля,
    в котором находится декорируемая функция, и времени создания файла."""

    def generate_file_name(func: Callable[..., Any]) -> str:
        """Генерирует имя файла на основе имени модуля и текущего времени."""
        module = inspect.getmodule(func)
        if module is None or module.__name__ in {"__main__", "<frozen runpy>", ""}:
            module_name = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0]
        else:
            module_name = module.__name__

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        return os.path.join(ROOT_PATH, "data", "output", f"{module_name}_{timestamp}.json")

    def inner(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Определяем имя файла
            final_file_name = file_name

            if final_file_name is not None and not isinstance(final_file_name, str):
                raise TypeError(
                    f"Имя файла сохранения: ожидался тип 'str', но получен '{type(final_file_name).__name__}'."
                )

            if final_file_name is None:
                final_file_name = generate_file_name(func)

            if not os.path.isabs(final_file_name):
                final_file_name = os.path.join(ROOT_PATH, final_file_name)

            if os.path.isdir(final_file_name):
                raise ValueError(f"Указан путь к директории '{final_file_name}', ожидался путь к файлу.")

            try:
                # Создаём директорию, если её нет
                os.makedirs(os.path.dirname(final_file_name), exist_ok=True)

                # Выполняем декорируемую функцию
                result = func(*args, **kwargs)

                # Пишем результат в файл
                with open(final_file_name, "w", encoding="utf-8") as f:
                    f.write(str(result))

                # print(f"Файл сохранен по пути: {final_file_name}")
                return result

            except Exception as e:
                raise RuntimeError(f"Ошибка при выполнении декорируемой функции или сохранении файла: {e}")

        return wrapper

    return inner


if __name__ == "__main__":
    print(f"ROOT_PATH: {ROOT_PATH}")
