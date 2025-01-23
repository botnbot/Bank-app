import os
import shutil
from typing import Generator
from unittest.mock import patch

import pytest

from config import ROOT_PATH
from src.decorators import save_to_file


@pytest.fixture(autouse=True)
def cleanup() -> Generator:
    """Очистка временных данных после каждого теста."""
    if os.path.exists(os.path.join(ROOT_PATH, "data", "output", "temp")):
        try:
            shutil.rmtree(os.path.join(ROOT_PATH, "data", "output", "temp"))
        except Exception as e:
            print(f"Ошибка при удалении временных файлов теста {e}")
    yield


def test_save_to_file_creates_file() -> None:
    """Тест: проверяем создание файла."""
    test_file = "test_output.json"

    @save_to_file(file_name=test_file)
    def sample_function() -> dict:
        return {"key": "value"}

    result = sample_function()

    expected_path = os.path.join(ROOT_PATH, test_file)
    assert os.path.exists(expected_path), "Файл не был создан."

    with open(expected_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert content == str(result), "Содержимое файла не совпадает с ожидаемым."
    os.remove(expected_path)


def test_save_to_file_generates_default_name() -> None:
    """Тест: проверяем генерацию имени файла по умолчанию."""

    @save_to_file()
    def sample_function() -> str:
        return "default_name_test"

    with patch("time.strftime", return_value="20250101_120000"):
        result = sample_function()

    generated_file_name = os.path.join(ROOT_PATH, "data", "output", "tests.test_decorators_20250101_120000.json")
    assert os.path.exists(generated_file_name), "Файл с именем по умолчанию не был создан."

    with open(generated_file_name, "r", encoding="utf-8") as f:
        content = f.read()
        assert content == str(result), "Содержимое файла с именем по умолчанию не совпадает с ожидаемым."
    os.remove(generated_file_name)


def test_save_to_file_invalid_file_name() -> None:
    """Тест: проверяем обработку некорректного пути файла."""
    invalid_file_name = os.path.join(ROOT_PATH, "")

    @save_to_file(file_name=invalid_file_name)
    def sample_function() -> str:
        return "test_invalid_file"

    with pytest.raises(ValueError, match="Указанный путь является директорией, ожидался файл."):
        sample_function()


def test_save_to_file_non_str_file_name() -> None:
    """Тест: проверяем обработку нестрокового имени файла."""

    @save_to_file(file_name=12345)
    def sample_function() -> str:
        return "test_invalid_type"

    with pytest.raises(TypeError, match="Имя файла должно быть строкой, получено: int"):
        sample_function()


def test_save_to_file_handles_exceptions() -> None:
    """Тест: проверяем обработку исключений внутри функции."""

    @save_to_file(file_name="exception_test.json")
    def sample_function() -> None:
        raise ValueError("Ошибка внутри функции")

    with pytest.raises(RuntimeError, match="Ошибка в функции или при сохранении файла"):
        sample_function()
