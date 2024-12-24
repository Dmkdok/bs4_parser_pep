import logging
from argparse import ArgumentParser

from constants import LOG_FORMAT


def configure_logging():
    """Настраивает логгирование."""

    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        filename='parser.log',
        encoding='utf-8',
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.getLogger().addHandler(console_handler)


def configure_argument_parser(available_modes):
    """Настраивает парсер аргументов командной строки."""
    parser = ArgumentParser()
    parser.add_argument(
        'mode', choices=available_modes, help='Режимы работы парсера'
    )
    parser.add_argument(
        '-c', '--clear-cache', action='store_true', help='Очистка кеша'
    )
    parser.add_argument(
        '-o',
        '--output',
        choices=('pretty', 'file'),
        help='Дополнительные способы вывода данных',
    )
    return parser
