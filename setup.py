from setuptools import setup

setup(
    name='scraper-boamp',
    version='1.0.0',
    description='Scraper for BOAMP data',
    url='https://github.com/michelbl/scraper-boamp',
    author='Michel Blancard',
    license='MIT',
    packages=['scraper_boamp'],
    install_requires=[
        'beautifulsoup4>=4.6.0',
        'jupyter>=1.0.0',
        'psycopg2-binary>=2.7.4',
        'requests>=2.18.4',
    ],
    zip_safe=False,
)
