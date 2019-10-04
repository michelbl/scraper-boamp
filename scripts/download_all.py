import psycopg2

from scraper_boamp.config import CONFIG_DATABASE
from scraper_boamp.to_database import stock_year_to_database, stream_year_to_database, STOCK_YEAR_LIST, STREAM_YEAR_LIST, STREAM_YEAR_CURRENT, URL_PART_STREAM, URL_PART_STREAM_CURRENT

# Open connection
connection = psycopg2.connect(
    dbname=CONFIG_DATABASE['name'],
    user=CONFIG_DATABASE['username'],
    password=CONFIG_DATABASE['password'],
)
cursor = connection.cursor()


for year in STOCK_YEAR_LIST:
    print(year)
    stock_year_to_database(connection, cursor)

for year in STREAM_YEAR_LIST:
    print(year)
    stream_year_to_database(year, URL_PART_STREAM, connection, cursor)

for year in STREAM_YEAR_CURRENT:
    print(year)
    stream_year_doctype_to_database(year=year, doc_type=None, url_part=URL_PART_STREAM_CURRENT, conection=connection, cursor=cursor)

cursor.close()
connection.close()
