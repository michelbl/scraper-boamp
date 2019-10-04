import os
import re
import zipfile
import tarfile
import shutil

import requests
from bs4 import BeautifulSoup

from scraper_boamp.config import CONFIG_FILE_STORAGE


# J = ?
# N = ?
# AO = Appel d'Offre
# IC-AA = Intention de Conclure - Avis d'Attribution
DOC_TYPE_LIST = [
    'BOAMP-J-AO',
    'BOAMP-J-IC-AA',
    'BOAMP-N-AO',
    'BOAMP-N-IC-AA',
    'MAPA-AO',
    'MAPA-IC-AA',
]

URL_BASE = 'https://echanges.dila.gouv.fr'
URL_PART_STOCK = '/OPENDATA/BOAMP/FluxHistorique/Boamp_v230/'
URL_PART_STREAM = '/OPENDATA/BOAMP/FluxHistorique/Boamp_v230/'
URL_PART_STREAM_CURRENT = '/OPENDATA/BOAMP/'

TMP_DIR = CONFIG_FILE_STORAGE['tmp_directory']

STOCK_YEAR_LIST = [] #[2015, 2016]
STREAM_YEAR_LIST = [2017, 2018]
STREAM_YEAR_CURRENT = [2019]


def stock_year_to_database(connection, cursor):
    for doc_type in DOC_TYPE_LIST:
        print(doc_type)
        stock_doctype_to_database(year=year, doc_type=doc_type, connection=connection, cursor=cursor)


def stock_year_doctype_to_database(year, doc_type, connection, cursor):
    os.mkdir(TMP_DIR)

    url_part_year = str(year) + '/'
    url_part_doc_type = doc_type + '/'
    archive_name = 'xml.zip'
    url_archive = URL_BASE + URL_PART_STOCK + url_part_year + url_part_doc_type + archive_name

    response_archive = requests.get(url_archive, stream=True)
    assert response_archive.status_code == 200

    content_type = response_archive.headers['Content-Type']
    assert content_type in {'application/octet-stream', 'application/zip'}, response_archive.headers

    archive_filename = os.path.join(TMP_DIR, archive_name)
    with open(archive_filename, 'wb') as file_object:
        for chunk in response_archive.iter_content(8192):
            file_object.write(chunk)

    unzip_dir = os.path.join(TMP_DIR, 'unzip')
    os.mkdir(unzip_dir)
    with zipfile.ZipFile(archive_filename, "r") as zip_ref:
        zip_ref.extractall(unzip_dir)
    assert os.listdir(unzip_dir) == ['xml']

    xml_dir = os.path.join(unzip_dir, 'xml')

    xml_filename_list = os.listdir(xml_dir)
    for xml_filename in xml_filename_list:
        avis_to_database(year, doc_type, xml_dir, xml_filename, connection, cursor)

    shutil.rmtree(TMP_DIR)


def stream_year_to_database(year, url_part, connection, cursor):
    for doc_type in DOC_TYPE_LIST:
        stream_year_doctype_to_database(year, doc_type, url_part, connection, cursor)


def stream_year_doctype_to_database(year, doc_type, url_part, connection, cursor):
    if doc_type:
        url = URL_BASE + url_part + str(year) + '/' + doc_type + '/'
    else:
        url = URL_BASE + url_part + str(year) + '/'

    print(url)
    response_year = requests.get(url)
    assert response_year.status_code == 200, (response_year.status_code, url)

    soup = BeautifulSoup(response_year.text, 'html.parser')

    links = soup.find_all('a')
    href_list = [
        link.attrs['href']
        for link in links
        if 'href' in link.attrs
    ]
    href_list_ok = [
        href
        for href in href_list
        if href[0] == 'B' #and href != '/OPENDATA/BOAMP/2018/BOAMP-N-IC-AA_2018_043008/'
    ]

    for href in href_list_ok:
        os.mkdir(TMP_DIR)
        stream_file_to_database(year, doc_type, href, url_part, connection, cursor)
        shutil.rmtree(TMP_DIR)


def stream_file_to_database(year, doc_type, filename, url_part, connection, cursor):    
    def check_stream_file_already_done(url, connection, cursor):
        cursor.execute("SELECT url FROM boamp_source_archives WHERE url = %s;", (url, ))
        results = cursor.fetchall()
        if len(results):
            return True

        cursor.execute("INSERT INTO boamp_source_archives (url) VALUES (%s)", (url, ))
        connection.commit()

        return False

    if doc_type:
        url_archive = URL_BASE + url_part + str(year) + '/' + doc_type + '/' + filename
    else:
        url_archive = URL_BASE + url_part + str(year) + '/' + filename

    if check_stream_file_already_done(url_archive, connection, cursor):
        return


    doc_type, year_bis, ident = re.match(r'^([A-Z\-]+)_(\d{4})_(\d+)\.taz$', filename).groups()
    assert year_bis == str(year)

    response_archive = requests.get(url_archive, stream=True)
    assert response_archive.status_code == 200, (response_archive.status_code, url_archive)

    #content_type = response_archive.headers['Content-Type']
    #assert content_type in {'application/octet-stream'}, response_archive.headers

    archive_file_path = os.path.join(TMP_DIR, 'file.taz')
    with open(archive_file_path, 'wb') as file_object:
        for chunk in response_archive.iter_content(8192):
            file_object.write(chunk)

    unzip_dir = os.path.join(TMP_DIR, 'unzip')
    os.mkdir(unzip_dir)
    with zipfile.ZipFile(archive_file_path, "r") as zip_ref:
        zip_ref.extractall(unzip_dir)

    archive_filename_2 = '{}_{}_{}.tar'.format(doc_type, year, ident)
    archive_file_path_2 = os.path.join(unzip_dir, archive_filename_2)
    assert os.listdir(unzip_dir) == [archive_filename_2]

    unzip_dir_2 = os.path.join(TMP_DIR, 'unzip_2')
    os.mkdir(unzip_dir_2)


    with tarfile.TarFile(archive_file_path_2, "r") as tar_ref:
        tar_ref.extractall(unzip_dir_2)

    uncompressed_dir_name = '{}_{}_{}'.format(doc_type, year, ident)
    uncompressed_dir_path = os.path.join(unzip_dir_2, uncompressed_dir_name)
    assert os.listdir(unzip_dir_2) == [uncompressed_dir_name]

    sorted_filename_list = sorted(os.listdir(uncompressed_dir_path))
    assert len(sorted_filename_list) % 2 == 0

    html_list = sorted_filename_list[::2]
    xml_list = sorted_filename_list[1::2]
    for filename_html, filename_xml in zip(html_list, xml_list):
        ident = re.match(r'^(\d{2}-\d+)\.html$', filename_html).groups()[0]
        assert filename_xml == ident + '.xml'

        avis_to_database(year, doc_type, uncompressed_dir_path, filename_xml, connection, cursor)


def avis_to_database(year, doc_type, xml_dir, xml_filename, connection, cursor):

    ident = re.match(r'^(\d{2}-\d+)\.xml$', xml_filename).groups()[0]

    xml_file_path = os.path.join(xml_dir, xml_filename)
    with open(xml_file_path, 'r') as f:
        xml_content = f.read()

    cursor.execute(
        """
        INSERT INTO boamp (
            year, doc_type, ident, xml_content
            )
            VALUES (
            %s, %s, %s, %s
           )""",
        (year, doc_type, ident, xml_content)
    )
    connection.commit()
