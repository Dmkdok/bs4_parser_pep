import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from exceptions import ParserFindTagException
from constants import PEP_URL


def get_response(session, url):
    """
    Выполняет GET-запрос к указанному URL и возвращает объект ответа.
    """
    try:
        response = session.get(url)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе к {url}: {e}")
        raise


def get_soup(session, url):
    """
    Получает HTML-контент страницы и возвращает объект BeautifulSoup.

    Выполняет GET-запрос по указанному URL, обрабатывает ответ и создает
    объект BeautifulSoup для парсинга HTML.
    Устанавливает кодировку ответа в utf-8.
    """
    try:
        response = get_response(session, url)
        response.encoding = 'utf-8'
        return BeautifulSoup(response.text, 'lxml')
    except requests.RequestException as e:
        logging.error(f"Ошибка при получении soup с {url}: {e}")
        raise


def find_tag(soup, tag_name, attrs=None):
    """
    Находит первый тег с заданными параметрами.
    Выбрасывает исключение, если тег не найден.
    """
    tag = soup.find(tag_name, attrs=attrs)
    if tag is None:
        raise ParserFindTagException(f'Не найден тег {tag_name} {attrs}')
    return tag


def get_pep_status(session, pep_url_suffix):
    """Извлекает статус PEP со страницы PEP."""

    pep_page = get_soup(session, urljoin(PEP_URL, pep_url_suffix))
    pep_content_section = find_tag(pep_page, 'section', {'id': 'pep-content'})
    pep_content_html = str(pep_content_section.dl)
    pep_content_soup = BeautifulSoup(pep_content_html, 'lxml')
    status_dd_tag = pep_content_soup.select_one(
        'dt:-soup-contains("Status") + dd'
    )
    if not status_dd_tag:
        raise ParserFindTagException('Не найден тег dd после dt с "Status"')

    return status_dd_tag.text.strip()
