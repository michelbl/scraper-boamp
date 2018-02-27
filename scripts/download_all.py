import psycopg2

from scraper_boamp.config import CONFIG_DATABASE
from scraper_boamp.to_database import stock_to_database, stream_to_database


# Open connection
connection = psycopg2.connect(
    dbname=CONFIG_DATABASE['name'],
    user=CONFIG_DATABASE['username'],
    password=CONFIG_DATABASE['password'],
)
cursor = connection.cursor()

stock_to_database(connection, cursor)
stream_to_database(connection, cursor)

cursor.close()
connection.close()
