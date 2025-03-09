import logging
from unittest.mock import patch

import pytest
from _pytest.logging import LogCaptureFixture

from src.services import investment_bank


@pytest.fixture
def mock_transactions():
    return [
        {"Дата операции": "2018-01", "Сумма операции": 124},
        {"Дата операции": "2018-04", "Сумма операции": 567},
        {"Дата операции": "2019-01", "Сумма операции": 890},
        {"Дата операции": "2018-04", "Сумма операции": 123},
    ]


def test_piggy_bank_correct_data(mock_transactions) -> None:
    """Успешный тест с корректными аргументами"""
    result = investment_bank("2018-04", mock_transactions, 50)
    expected_result = 60
    assert result == expected_result


def test_piggy_bank_incorrect_date(mock_transactions) -> None:
    """Тест передачи некорректной даты в качестве аргумента"""
    with pytest.raises(ValueError):
        investment_bank("2018-14", mock_transactions, 50)


def test_piggy_bank_missing_date_in_DataFrame() -> None:
    """Тест передачи DataFrame с пропущенными датами в качестве аргумента"""
    mock_transactions = [
        {"Дата операции": "NaT", "Сумма операции": 567},
        {"Дата операции": "", "Сумма операции": 537},
        {"Дата операции": "2019-01", "Сумма операции": 890},
        {"Дата операции": "2018-04", "Сумма операции": 123},
    ]
    result = investment_bank("2018-04", mock_transactions, 50)
    expected_result = 27
    assert result == expected_result


def test_logging_permission_error(caplog: LogCaptureFixture) -> None:
    # Мокируем os.makedirs и FileHandler, чтобы вызвать PermissionError
    with patch("os.makedirs"), patch("logging.FileHandler", side_effect=PermissionError("No permission")):
        from src.services import loger

        loger.handlers.clear()

        # Устанавливаем уровень логирования и запускаем код
        with caplog.at_level(logging.ERROR, logger="investment_bank"):
            from importlib import reload
            import src.services

            reload(src.services)

        # Проверяем, что сообщение об ошибке было записано в логи
        assert "Ошибка доступа к файлу логов: No permission" in caplog.text
