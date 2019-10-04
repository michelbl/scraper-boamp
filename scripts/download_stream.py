import psycopg2

from scraper_boamp.config import CONFIG_DATABASE
from scraper_boamp.to_database import stream_year_doctype_to_database, URL_PART_STREAM_CURRENT

CURRENT_YEAR = 2019

# Open connection
connection = psycopg2.connect(
    dbname=CONFIG_DATABASE['name'],
    user=CONFIG_DATABASE['username'],
    password=CONFIG_DATABASE['password'],
)
cursor = connection.cursor()

stream_year_doctype_to_database(year=CURRENT_YEAR, doc_type=None, url_part=URL_PART_STREAM_CURRENT, connection=connection, cursor=cursor)

cursor.close()
connection.close()
