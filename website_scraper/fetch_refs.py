import re
import math
import datetime
import os
import configparser
import json
import sys

import requests
from bs4 import BeautifulSoup


base_dir = os.path.dirname(os.path.realpath(__file__))
#base_dir = os.getcwd()  # notebook
base_dir


# Read config

config = configparser.ConfigParser()
config_path = os.path.join(base_dir, 'config.ini')
config.read(config_path)
refs_dir = config['boamp']['refs_dir']


# Constants

link_avis_regex = r'^/avis/detail/(.*)$'
famille_types = ['MAPA', 'FNS', 'JOUE', 'DSP']
descripteur_cat_list = ['da10', 'da20', 'da30', 'da40', 'da50', 'da60', 'da70', 'da80', 'da90', 'da100', 'da110', 'da120', 'da130', 'da140']
ref_per_page = 10

class TooManyResultsException(Exception):
    pass


# Functions


def get_cookie():
    regex_cookie = r'(eZSESSID1335d27b6a308a5b0435f39d334a4390=[a-z\d]+);'

    url = 'http://www.boamp.fr/'
    r = requests.get(url)
    assert r.status_code == 200
    cookie = r.headers['Set-Cookie']
    cookie = re.search(regex_cookie, cookie).groups()[0]
    return cookie


def fetch_year(cookie, year):
    for day in get_dates_from_year(year):
        try:
            fetch_date(cookie, day)
        except TooManyResultsException as e:
            print("Warning: too many results for day {}".format(day))


def get_dates_from_year(year):
    d1 = datetime.date(year, 1, 1)
    d2 = datetime.date(year+1, 1, 1)

    delta = d2 - d1

    days = []
    for i in range(delta.days):
        day = d1 + datetime.timedelta(days=i)
        days.append(day)
    
    return days


def fetch_date(cookie, day):
    filepath = os.path.join(refs_dir, str(day))
    if os.path.isfile(filepath):
        return
    
    day_str = day.strftime('%d/%m/%Y')
    
    nb_results = start_search(cookie, day_str, '')
    
    if nb_results > 500:
        try:
            results = search_by_famille(cookie, day_str)
        except TooManyResultsException:
            results = search_by_descripteur(cookie)
    else:
        results = fetch_from_search(cookie, nb_results)

    # Some avis can belong to several categories
    results = list(set(results))
        
    with open(filepath, 'w') as f:
        json.dump(results, f)


def start_search(cookie, day_str, famille):
    form_data = {
        'estrecherchesimple': 0,
        'archive': 1,
        'idweb': '',
        'nomacheteur': '',
        'fulltext': '',
        'dateparutionmin': day_str,
        'dateparutionmax': day_str,
        'famille': famille,  # MAPA, FNS, JOUE
        'prestataire': '',
    }
    headers = {
        'Cookie': cookie,
    }
    url = 'http://www.boamp.fr/avis/liste'
    r = requests.post(url, headers=headers, data=form_data)
    assert r.status_code == 200

    nb_results = extract_nb_results(r)
    
    return nb_results

        
def search_by_famille(cookie, day_str):
    results = []
    for famille in famille_types:
        nb_results_famille = start_search(cookie, day_str, famille)
        if nb_results_famille > 500:
            raise TooManyResultsException()
        results_famille = fetch_from_search(cookie, nb_results_famille)
        results += results_famille
    return results


def search_by_descripteur(cookie):
    results = []
    for descripteur_cat in descripteur_cat_list:
        results_descripteur = refine_search(cookie, descripteur_cat)
        results += results_descripteur
    results = list(set(results))
    return results


def refine_search(cookie, descripteur_cat):
    url = 'http://www.boamp.fr/avis/tri?refine=f/classementdescripteur_cat/{}'.format(descripteur_cat)
    headers = {
        'Cookie': cookie,
    }
    r = requests.get(url, headers=headers)
    assert r.status_code == 200
    
    nb_results = extract_nb_results(r)
    if nb_results > 500:
        raise TooManyResultsException()
    
    results = fetch_from_search(cookie, nb_results)
    
    url = 'http://www.boamp.fr/avis/tri?cancelrefine=f/classementdescripteur_cat/{}'.format(descripteur_cat)
    headers = {
        'Cookie': cookie,
    }
    r = requests.get(url, headers=headers)
    assert r.status_code == 200
    
    return results


def fetch_from_search(cookie, nb_results):
    nb_pages = math.ceil(nb_results/ref_per_page)
    
    refs = []
    for i_page in range(nb_pages):
        refs_page = request_page(cookie, i_page)
        refs = refs + refs_page
    return refs


        
def request_page(cookie, i_page):
    url = 'http://www.boamp.fr/avis/page?page={}'.format(i_page+1)
    headers = {
        'Cookie': cookie,
    }
    r = requests.get(url, headers=headers)
    assert r.status_code == 200

    return extract_refs(r)


def extract_nb_results(r):
    soup = BeautifulSoup(r.text, 'html.parser')
    
    regex_nb_results = r'\sRésultats : (\d+)\s'
    text_nb_results = soup.find('div', class_='search-result-caption').find('h2').text
    nb_results_str = re.search(regex_nb_results, text_nb_results).groups()[0]
    nb_results = int(nb_results_str)
    return nb_results


def extract_links(request_result, regex):
    page = request_result.text
    soup = BeautifulSoup(page, 'html.parser')
    links = soup.find_all('a')
    hrefs = [link.attrs['href'] for link in links if 'href' in link.attrs]
    hrefs_clean = [href for href in hrefs if re.match(regex, href)]
    return hrefs_clean


def extract_refs(r):
    links = set(extract_links(r, link_avis_regex))
    return [re.match(link_avis_regex, link).groups()[0] for link in links]


## Does not work
#
#form_data = {
#    'hf': 50,
#}
#headers = {
#    'Cookie': cookie
#}
#url = 'http://www.boamp.fr/avis/tri'
#r = requests.post(url, data=form_data)
#assert r.status_code == 200


# Script

assert len(sys.argv) == 2
year = int(sys.argv[1])

cookie = get_cookie()
fetch_year(cookie, year)
