import logging

import pytest

from utils.ml_logging import KEYINFO_LEVEL_NUM, get_logger


# Patch the logging module during the tests to capture log records
@pytest.fixture
def caplog(caplog):
    """
    Set the logging level to DEBUG for the duration of the tests.

    :param caplog: pytest's built-in fixture for capturing log messages.
    :return: caplog with the logging level set to DEBUG.
    """
    caplog.set_level(logging.DEBUG)
    return caplog


def test_get_logger_default_level(caplog):
    """
    Test that the get_logger function correctly logs INFO messages.

    :param caplog: pytest's built-in fixture for capturing log messages.
    """
    logger = get_logger()
    test_message = "This is an INFO message"

    logger.info(test_message)

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "INFO"
    assert caplog.records[0].msg == test_message


def test_get_logger_custom_level(caplog):
    """
    Test that the get_logger function correctly logs WARNING messages when the level is set to WARNING.

    :param caplog: pytest's built-in fixture for capturing log messages.
    """
    logger = get_logger(level=logging.WARNING)
    test_message = "This is a WARNING message"

    logger.warning(test_message)

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"
    assert caplog.records[0].msg == test_message


def test_get_logger_keyinfo_level(caplog):
    """
    Test that the get_logger function correctly logs KEYINFO messages when the level is set to KEYINFO.

    :param caplog: pytest's built-in fixture for capturing log messages.
    """
    logger = get_logger(level=KEYINFO_LEVEL_NUM)
    test_message = "This is a KEYINFO message"

    logger.log(KEYINFO_LEVEL_NUM, test_message)

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "KEYINFO"
    assert caplog.records[0].msg == test_message
