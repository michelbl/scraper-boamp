# scraper-boamp

Download data from BOAMP!
* https://www.data.gouv.fr/fr/datasets/boamp/
* https://echanges.dila.gouv.fr/OPENDATA/BOAMP/


## Install `scaper-boamp`

### Prerequisites

* Install `postgresql`>=9.0 (may work on prior versions). Make sure it uses UTF-8 encoding.
* Create a python virtual env with python3 (I suggest using `pew`; works for python >=3.6, may work for prior versions).


### Installation

```
git clone https://github.com/michelbl/scraper-boamp
pip install --editable .
```
* Copy `config.ini.example` to `config.ini` and set your configuration.
* Make sure `tmp_directory` foes not exist but its parent exists.

### Database

* Create a new database user with all privileges on a new table, with access by password (`md5` in `pg_hda.conf`).

```
sudo -u postgres createuser --login --pwprompt boamp
sudo -u postgres createdb --owner=boamp boamp
```

then:

```
CREATE TABLE boamp (year int, doc_type text, ident text, xml_content text);
CREATE INDEX ON boamp (ident);
CREATE TABLE boamp_source_archives (url text);
CREATE INDEX ON boamp_source_archives (url);
```


## Usage

```
python scripts/download_all.py
```

It takes about 1 hour to process years 2015, 2016, 2017 (about 500,000 avis).

Then periodically:

```
python scripts/download_stream.py
```

For example, in `/etc/crontab`:

```
52 5 * * * michel /home/michel/.local/share/virtualenvs/place/bin/python /home/michel/place/scraper-boamp/scripts/download_stream.py
```


## See also

* https://www.data.gouv.fr/fr/datasets/marches-publics-conclus-recenses-sur-la-plateforme-des-achats-de-letat/
* https://www.data.gouv.fr/fr/datasets/referentiel-de-donnees-marches-publics/
* http://www.efj.press/simonstephan/enquete-sur-les-marches-publics/
