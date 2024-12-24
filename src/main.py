import logging
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urljoin

import requests
import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, PEP_URL
from outputs import control_output
from exceptions import VersionsNotFound
from utils import find_tag, get_pep_status, get_soup


def whats_new(session):
    """
    Собирает информацию о нововведениях в разных версиях Python.

    Возвращает список кортежей, где каждый кортеж содержит ссылку на статью,
    заголовок и информацию о редакторе/авторе.
    """
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    soup = get_soup(session, whats_new_url)
    if not soup:
        logging.error(f'Не удалось получить страницу {whats_new_url}')
        return None
    main_div = find_tag(soup, 'section', {'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', {'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all('li', {'class': 'toctree-l1'})

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = section.find('a')
        version_link = urljoin(whats_new_url, version_a_tag['href'])
        response = session.get(version_link)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')
        h1 = soup.find('h1')
        dl = soup.find('dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append((version_link, h1.text, dl_text))
    return results


def latest_versions(session):
    """
    Собирает информацию о последних версиях Python.

    Возвращает список кортежей,
    где каждый кортеж содержит ссылку на документацию,
    версию и статус.
    """
    soup = get_soup(session, MAIN_DOC_URL)
    if not soup:
        logging.error(f'Не удалось получить страницу {MAIN_DOC_URL}')
        return None
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise VersionsNotFound('Не найден список c версиями Python')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))

    return results


def download(session):
    """Скачивает архив документации Python."""
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    soup = get_soup(session, downloads_url)
    if not soup:
        logging.error(f'Не удалось получить страницу {downloads_url}')

    main_tag = soup.find('div', {'role': 'main'})
    table_tag = main_tag.find('table', {'class': 'docutils'})
    pdf_a4_tag = table_tag.find('a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = Path(archive_url).name
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(parents=True, exist_ok=True)
    archive_path = downloads_dir / filename

    try:
        response = session.get(archive_url, stream=True)
        response.raise_for_status()

        with open(archive_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logging.info(f'Архив был загружен и сохранён: {archive_path}')

    except requests.exceptions.RequestException as e:
        logging.error(f'Ошибка при загрузке архива {archive_url}: {e}')


def pep(session):
    """
    Собирает информацию о статусах всех PEP
    и возвращает результаты в виде списка кортежей.

    Функция парсит страницу со списком PEP, извлекает статус каждого PEP
    и подсчитывает количество PEP с каждым статусом.
    """

    pep_page = get_soup(session, PEP_URL)
    if not pep_page:
        logging.error(f'Не удалось получить страницу {PEP_URL}')
    pep_table_section = find_tag(
        pep_page, 'section', {'id': 'index-by-category'}
    )
    pep_table_bodies = pep_table_section.find_all('tbody')
    pep_status_counts = defaultdict(int)
    results = [('Статус', 'Количество')]

    for table_body in tqdm(pep_table_bodies):
        rows = table_body.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            pep_status_preview = cells[0].text[1:]
            pep_relative_link = cells[1].a['href']
            pep_full_status = get_pep_status(session, pep_relative_link)
            expected_statuses = EXPECTED_STATUS[pep_status_preview]
            if pep_full_status not in expected_statuses:
                logging.info(
                    'Несовпадающие статусы:\n'
                    f'{urljoin(PEP_URL, pep_relative_link)}\n'
                    f'Статус в карточке: {pep_full_status}\n'
                    f'Ожидаемые статусы: {expected_statuses}'
                )
            pep_status_counts[pep_full_status] += 1

    for status, count in pep_status_counts.items():
        results.append((status, count))
    results.append(('Total', sum(pep_status_counts.values())))

    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    """Основная функция парсера."""

    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode

    try:
        results = MODE_TO_FUNCTION[parser_mode](session)
        if results is not None:
            control_output(results, args)

    except Exception as e:
        logging.exception(f'Ошибка в работе парсера: {e}', stack_info=True)

    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
