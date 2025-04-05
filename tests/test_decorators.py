import json
import os
import shutil
from typing import Any, Generator
from unittest.mock import patch

import pytest

from config import ROOT_PATH
from src.decorators import save_to_file


@pytest.fixture(autouse=True)
def cleanup() -> Generator:
    """Очистка временных данных после каждого теста."""
    output_dir = os.path.join(ROOT_PATH, "data", "output")
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            print(f"Ошибка при удалении временных файлов теста: {e}")
    yield


def read_json(file_path: str) -> Any:
    """Читает JSON-файл и возвращает его содержимое."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_save_to_file_creates_file() -> None:
    """Тест: проверяем создание файла с заданным именем."""
    test_file = "test_output.json"

    @save_to_file(file_name=test_file)
    def sample_function() -> dict:
        return {"key": "value"}

    result = sample_function()
    expected_path = os.path.join(ROOT_PATH, test_file)

    assert os.path.exists(expected_path), "Файл не был создан."
    assert read_json(expected_path) == result, "Содержимое файла не совпадает с ожидаемым."
    os.remove(expected_path)


def test_save_to_file_generates_default_name() -> None:
    """Тест: проверяем генерацию имени файла по умолчанию."""

    @save_to_file()
    def sample_function() -> str:
        return "default_name_test"

    with patch("time.strftime", return_value="20250101_120000"):
        result = sample_function()

    module_name = "test_decorators"
    generated_file_name = os.path.join(ROOT_PATH, "data", "output", f"{module_name}_20250101_120000.json")

    assert os.path.exists(generated_file_name), "Файл с именем по умолчанию не был создан."

    with open(generated_file_name, "r", encoding="utf-8") as f:
        content = json.load(f)
        assert content == result, "Содержимое файла с именем по умолчанию не совпадает с ожидаемым."
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


def test_save_to_file_from_different_module() -> None:
    """Тест: проверяем имя файла для функции из другого модуля."""

    @save_to_file()
    def external_function() -> str:
        return "external_module_test"

    with patch("time.strftime", return_value="20250101_120000"):
        result = external_function()

    module_name = "test_decorators"
    generated_file_name = os.path.join(ROOT_PATH, "data", "output", f"{module_name}_20250101_120000.json")

    assert os.path.exists(generated_file_name), "Файл с именем функции из другого модуля не был создан."
    with open(generated_file_name, "r", encoding="utf-8") as f:
        content = json.load(f)
        assert content == result, "Содержимое файла не совпадает с ожидаемым."
    os.remove(generated_file_name)
