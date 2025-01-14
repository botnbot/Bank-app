import inspect
import os
import time
from functools import wraps
from typing import Any, Callable, Optional
from config import ROOT_PATH

def save_to_file(file_name: Optional[str] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Декоратор, который записывает в файл результат, возвращаемый функцией. Файл находится по пути data/output/,
    имя файла состоит из названия модуля, в котором находится декорируемая функция и времени создания файла"""

    def inner(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Определяем имя файла, если оно не задано
            nonlocal file_name
            if file_name is None:
                module = inspect.getmodule(func)
                if module is None or module.__name__ in {"__main__", "<frozen runpy>"}:
                    # Если модуль — __main__ или <frozen runpy>, используем имя текущего скрипта
                    module_name = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0]
                else:
                    module_name = module.__name__
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                file_name = os.path.join(ROOT_PATH,rf"data\output\{module_name}_{timestamp}.json")
            # Создаём директорию, если её нет
            os.makedirs(os.path.dirname(file_name), exist_ok=True)

            result = func(*args, **kwargs)
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(str(result))
            return result

        return wrapper

    return inner
