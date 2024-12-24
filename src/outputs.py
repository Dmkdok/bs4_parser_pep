import csv
import datetime

from prettytable import PrettyTable

from constants import BASE_DIR, DATETIME_FORMAT


def print_results(results):
    """Выводит результаты в консоль."""
    for row in results:
        print(*row)


def control_output(results, args):
    """
    Управляет выводом результатов в зависимости от аргументов командной строки.
    Вызывает соответствующую функцию вывода на основе значения `args.output`
    """

    if args.output == 'pretty':
        pretty_output(results)
    elif args.output == 'file':
        file_output(results, args)
    else:
        print_results(results)


def file_output(results, args):
    """Сохраняет результаты в CSV файл."""

    results_dir = BASE_DIR / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    parser_mode = args.mode
    now = datetime.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now_formatted}.csv'
    file_path = results_dir / file_name
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(results)
        print(f'Результаты сохранены в файл {file_path}')
    except Exception as e:
        print(f'Ошибка при сохранении результатов в файл: {e}')


def pretty_output(results):
    """Выводит результаты в виде красивой таблицы."""

    if not results:
        print('Нет данных для вывода.')
        return

    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'

    for row in results[1:]:
        table.add_row(row)

    print(table)
