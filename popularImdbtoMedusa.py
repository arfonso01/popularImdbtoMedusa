import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
import logging

min_rating = 8.5
min_year = 2020
medusa_host = 'localhost:8081'
medusa_api_key = 'my_medusa_api_key'
medusa_indexer = "tmdb" # or "tvdb" or "imdb"

exclude_series = Path('exclude_series.txt')
exclude_series.touch(exist_ok=True)
exclude = map(lambda x: str.strip(x[2:]), open('exclude_series.txt').readlines())

headers_for_medusa = {
    'Content-Type': 'application/json',
    'Accept': 'application/json; charset=UTF-8',
    'x-api-key': medusa_api_key}

imdburl = 'https://www.imdb.com/search/title/?title_type=tv_series'
request = requests.get(imdburl)

soup = BeautifulSoup((request).text, 'html.parser')

div_items = soup.find_all('div', {'class': 'lister-item-content'})

title = list(map(lambda x: x.find('a').text, div_items))
year = list(map(lambda x:
                int(x.find(class_='lister-item-year text-muted unbold').text[1:5]), div_items))

ratings = list(map(lambda x: str(x.find('strong'))[8:11], div_items))
imdbid_raw = list(map(lambda x: str(x.find('a'))[16:26], div_items))
imdbid = list(map(lambda x: x if x[9] != '/' else x[0:9], imdbid_raw))
id_less_tt = list(map(lambda x: x[2:], imdbid))

tvdb_domain = 'https://thetvdb.com/api/GetSeriesByRemoteID.php?imdbid='
tmdb_domain = 'https://www.themoviedb.org/search/tv?query='
tvdbid_list = []
tmdbid_list = []

series_table = []

def tvdburl(ndir):
    return tvdb_domain + imdbid[ndir]

def tmdb_url(ndir):
    return tmdb_domain + title[ndir] + ' ' + 'y:' + str(year[ndir]) #+ '&language=es'

def db_request(ndir, db_url):
    return requests.get(db_url(ndir))

def db_soup(ndir, db_url):
    return BeautifulSoup((db_request(ndir, db_url)).text, 'lxml')

def tvdb_id_finder(ndir, tvdburl):
    return db_soup(ndir, tvdburl).find('seriesid').text

def tmdb_id_finder(ndir, tmdb_url):
    try:
        raw = db_soup(ndir, tmdb_url).find('a', attrs={'href': re.compile("^/tv/\d")})
        return str(raw.get('href'))[4:]
    except AttributeError:
        return '0'

def add_to_id_list(ndir, db_url, dbid_finder, id_list):
    yield id_list.append(dbid_finder(ndir, db_url))

def convert_imdb_to_other_id(ndir, db_url, dbid_finder, id_list):
    if ndir >= len(imdbid):
        return
    else:
        next(add_to_id_list(ndir, db_url, dbid_finder, id_list))
    convert_imdb_to_other_id(ndir+1, db_url, dbid_finder, id_list)

def filter_series_table(ndir):
    try:
        if int(year[ndir]) >= min_year and float(ratings[ndir]) >= min_rating and not id_less_tt[ndir] in exclude:

            yield series_table.append([title[ndir], year[ndir], ratings[ndir],
                                       imdbid[ndir], tvdbid_list[ndir], tmdbid_list[ndir]])
        else:
            yield
    except ValueError:
        yield

def series_table_iterate(ndir):
    if ndir >= len(imdbid):
        return
    else:
        next(filter_series_table(ndir))
    series_table_iterate(ndir+1)

def db_indexer(ndir, db_name):
    if db_name == 'imdb':
        return series_table[ndir][3][2:]
    if db_name == 'tvdb':
        return series_table[ndir][4]
    if db_name == 'tmdb':
        return series_table[ndir][5]

def medusa_request(bd_name, bd_id):
    return requests.get(medusa_host + '/api/v2/series/' +
                        str(bd_name) + str(bd_id) , headers = headers_for_medusa)

def status_code(bd_name, bd_id):
    return medusa_request(bd_name, bd_id).status_code

def add_to_medusa(ndir, db_name):
    data = {
        "id": {
            medusa_indexer: db_indexer(ndir, db_name)
        }
    }

    return requests.post(medusa_host + '/api/v2/series', json=data, headers=headers_for_medusa).status_code

def main(ndir):
    if status_code('imdb', db_indexer(ndir, 'imdb')) + status_code('tvdb', db_indexer(ndir, 'ivdb')) + status_code('tmdb', db_indexer(ndir, 'tmdb')) >= 1200 and int(series_table[ndir][5]) > 0:
        logging.info('Trying add ' + series_table[ndir][0] +
              ' (' + series_table[ndir][3] + ') '+
              'with ' + medusa_indexer)
        yield add_to_medusa(ndir, medusa_indexer)

    else:
        yield

def master(ndir):
    if ndir >= len(series_table):
        exit()
    else:
        next(main(ndir))

    master(ndir+1)

logging.basicConfig(
    filename='popularImdbtoMedusa.log',
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

convert_imdb_to_other_id(0, tvdburl, tvdb_id_finder, tvdbid_list)
convert_imdb_to_other_id(0, tmdb_url, tmdb_id_finder, tmdbid_list)

series_table_iterate(0)

master(0)
