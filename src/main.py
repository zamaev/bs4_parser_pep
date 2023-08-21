import logging
import re
from collections import Counter
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from outputs import control_output
from tqdm import tqdm
from utils import find_tag, get_response

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, PEPS_URL


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
                            'li', attrs={'class': 'toctree-l1'})
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append(
            (version_link, h1.text, dl_text)
        )
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (link, version, status)
        )
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    table_tag = find_tag(soup, 'table', attrs={'class': 'docutils'})
    pdf_a4_tag = find_tag(table_tag, 'a',
                          attrs={'href': re.compile(r'.+pdf-a4\.zip$')})
    archive_url = urljoin(downloads_url, pdf_a4_tag['href'])
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    peps_url = urljoin(PEPS_URL, 'pep-0000/')
    response = get_response(session, peps_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    section_tag = find_tag(soup, 'section', attrs={'id': 'numerical-index'})
    table_tag = find_tag(section_tag, 'table')
    tbody_tag = find_tag(table_tag, 'tbody')
    status_count = Counter()
    result = [('Статус', 'Количество')]
    mismatched_status_peps = []
    peps_total = 0
    for tr_tag in tqdm(tbody_tag.find_all('tr')):
        pep_status = find_tag(tr_tag, 'abbr').text[1:]
        pep_url = urljoin(PEPS_URL, find_tag(tr_tag, 'a')['href'])
        pep_page_status = str(get_pep_page_status(session, pep_url))
        status_count[pep_page_status] += 1
        peps_total += 1
        if pep_page_status not in EXPECTED_STATUS[pep_status]:
            mismatched_status_peps.append(
                (pep_url, pep_status, pep_page_status)
            )
    if mismatched_status_peps:
        log = 'Несовпадающие статусы:\n'
        for pep_url, pep_status, pep_page_status in mismatched_status_peps:
            expected_status = ', '.join(EXPECTED_STATUS[pep_status])
            log += (
                f'{pep_url}\n'
                f'Статус в карточке: {pep_page_status}\n'
                f'Ожидаемые статусы: [{expected_status}]\n'
            )
        logging.warn(log)
    result += status_count.most_common()
    result.append(('Total', peps_total))
    return result


def get_pep_page_status(session, pep_url):
    response = get_response(session, pep_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    dl_tag = find_tag(soup, 'dl')
    dt_tags = dl_tag.find_all('dt')
    for dt_tag in dt_tags:
        if dt_tag.text == 'Status:':
            return dt_tag.find_next_sibling().string


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
