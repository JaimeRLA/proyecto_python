import os
from collections.abc import Callable

import pandas as pd
from bs4 import BeautifulSoup
from bs4.element import Tag

from testing_common import test_docstring, test_doctests, test_type_hints, check_duplicated_ids


SITE = "https://datos.madrid.es"
DOWNLOADS_PATH = "/dataset/210104-0-multas-circulacion-detalle/downloads"

# Reference value computed independently from the real November 2023 file
# (2023_nov.csv, as downloaded from datos.madrid.es), not the anonymized
# data_test.csv sample used in earlier notebooks.
EXPECTED_NOV_2023_COUNT = 209657


def test_fetch_dataset_page(fetch_dataset_page: Callable):
    soup = fetch_dataset_page(SITE + DOWNLOADS_PATH)
    assert isinstance(soup, BeautifulSoup), "fetch_dataset_page must return a BeautifulSoup object"
    assert len(soup.find_all(attrs={'data-key': '2023-Noviembre'})) > 0, \
        "The parsed page should contain at least one block with data-key='2023-Noviembre'"
    print("test_fetch_dataset_page OK")


def test_fetch_dataset_page_typehints(fetch_dataset_page: Callable):
    test_type_hints(fetch_dataset_page, {str, BeautifulSoup})


def test_find_resource_block(find_resource_block: Callable, soup):
    block = find_resource_block(soup, 2023, 'nov')
    assert 'tracked-resource-item' in block.get('class', []), \
        "find_resource_block must return the 'tracked-resource-item' block"
    detalle_link = block.find('a', title='Detalle. Noviembre 2023')
    assert detalle_link is not None, \
        "The returned block must contain the 'Detalle. Noviembre 2023' link"
    agrupadas_link = block.find('a', title=lambda t: t and t.startswith('Agrupadas'))
    assert agrupadas_link is None, \
        "find_resource_block must not return the 'Agrupadas-excluidas' block"

    try:
        find_resource_block(soup, 1899, 'nov')
    except ValueError:
        pass
    else:
        raise AssertionError("find_resource_block should raise ValueError for a year with no data")

    print("test_find_resource_block OK")


def test_find_resource_block_typehints(find_resource_block: Callable):
    test_type_hints(find_resource_block, {BeautifulSoup, int, str, Tag})


def test_extract_download_url(extract_download_url: Callable):
    html = (
        '<div class="tracked-resource-item">'
        '<a href="/dataset/x/resource/y" title="Detalle. Enero 2026">Detalle</a>'
        '<a class="btn btn-primary resource-url-analytics resource-type-data" '
        'href="/dataset/x/resource/y/download/y.csv">Descarga</a>'
        '</div>'
    )
    block = BeautifulSoup(html, 'html.parser').find('div')
    expected = 'https://datos.madrid.es/dataset/x/resource/y/download/y.csv'
    result = extract_download_url(block)
    assert result == expected, f"Expected {expected!r}, got {result!r}"

    # Already-absolute hrefs should be returned unchanged
    html_abs = html.replace(
        'href="/dataset/x/resource/y/download/y.csv"',
        'href="https://datos.madrid.es/dataset/x/resource/y/download/y.csv"'
    )
    block_abs = BeautifulSoup(html_abs, 'html.parser').find('div')
    assert extract_download_url(block_abs) == expected, \
        "extract_download_url should not double-prefix an already-absolute URL"

    print("test_extract_download_url OK")


def test_extract_download_url_typehints(extract_download_url: Callable):
    test_type_hints(extract_download_url, {Tag, str})


def test_download_month_csv(download_month_csv: Callable):
    # Use a month other than 2023-nov so this test doesn't overwrite the
    # shared 2023_nov.csv fixture used by the other notebooks.
    filepath = download_month_csv(2023, 'oct')
    assert filepath == '2023_oct.csv', f"Expected '2023_oct.csv', got {filepath!r}"
    assert os.path.exists(filepath), f"{filepath} was not created"
    assert os.path.getsize(filepath) > 1_000_000, \
        f"{filepath} looks too small ({os.path.getsize(filepath)} bytes) for a full month of fines"

    # The saved file must be UTF-8 encoded, regardless of the source
    # encoding (iso-8859-15) used to decode resp.content.
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    header = content.splitlines()[0]
    assert header.startswith('CALIFICACION;LUGAR;MES;ANIO;HORA;IMP_BOL'), \
        f"Unexpected header: {header}"

    with open(filepath, 'rb') as f:
        raw = f.read()
    accented_utf8 = any(ch.encode('utf-8') in raw for ch in 'ÑÁÉÍÓÚñáéíóú')
    assert accented_utf8, \
        "Expected UTF-8-encoded accented characters in the saved file; it may " \
        "have been saved with the source encoding (iso-8859-15) instead of utf-8"

    print("test_download_month_csv OK")


def test_download_month_csv_typehints(download_month_csv: Callable):
    test_type_hints(download_month_csv, {int, str})


def test_get_data(get_data: Callable):
    # Fast path: this file already exists from earlier notebooks, so this
    # assertion does not require network access.
    assert os.path.exists('2023_nov.csv'), \
        "This test assumes 2023_nov.csv is already present (from E1_analisis_fichero.ipynb)"
    filepath = get_data(2023, 'nov')
    assert filepath == '2023_nov.csv', f"Expected '2023_nov.csv', got {filepath!r}"

    # Slow path: a month not yet downloaded must be fetched from the web.
    filepath2 = get_data(2023, 'dec')
    assert filepath2 == '2023_dec.csv', f"Expected '2023_dec.csv', got {filepath2!r}"
    assert os.path.exists(filepath2), f"{filepath2} was not created"

    print("test_get_data OK")


def test_get_data_typehints(get_data: Callable):
    test_type_hints(get_data, {int, str})


def test_month_range(month_range: Callable):
    assert month_range(2023, 'nov', 2024, 'feb') == [
        (2023, 'nov'), (2023, 'dec'), (2024, 'jan'), (2024, 'feb')
    ]
    assert month_range(2023, 'nov', 2023, 'nov') == [(2023, 'nov')]

    try:
        month_range(2024, 'feb', 2023, 'nov')
    except ValueError:
        pass
    else:
        raise AssertionError("month_range should raise ValueError when end is before start")

    print("test_month_range OK")


def test_month_range_typehints(month_range: Callable):
    test_type_hints(month_range, {int, str, list[tuple[int, str]]})


def test_download_all_data(download_all_data: Callable):
    result = download_all_data(2023, 'nov', 2023, 'nov')
    assert isinstance(result, pd.DataFrame), "download_all_data must return a pandas DataFrame"
    assert len(result) == EXPECTED_NOV_2023_COUNT, \
        f"Expected {EXPECTED_NOV_2023_COUNT} rows for 2023-nov, got {len(result)}"
    for col in ('CALIFICACION', 'LUGAR', 'IMP_BOL', 'DENUNCIANTE'):
        assert col in result.columns, f"Missing column '{col}'"

    multi = download_all_data(2023, 'nov', 2023, 'dec')
    assert len(multi) > len(result), \
        "Combining two months should yield more rows than a single month"
    assert list(multi.index) == list(range(len(multi))), \
        "download_all_data must reset the index after concatenating (pd.concat(..., ignore_index=True))"

    print("test_download_all_data OK")


def test_download_all_data_typehints(download_all_data: Callable):
    test_type_hints(download_all_data, {int, str, pd.DataFrame})
