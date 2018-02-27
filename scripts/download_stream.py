import psycopg2

from scraper_boamp.config import CONFIG_DATABASE
from scraper_boamp.to_database import stream_year_to_database

CURRENT_YEAR = 2018


# Open connection
connection = psycopg2.connect(
    dbname=CONFIG_DATABASE['name'],
    user=CONFIG_DATABASE['username'],
    password=CONFIG_DATABASE['password'],
)
cursor = connection.cursor()

stream_year_to_database(CURRENT_YEAR, connection, cursor)

cursor.close()
connection.close()
