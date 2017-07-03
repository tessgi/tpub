# tpub: TESS publication database

***A database of scientific publications related to NASA's TESS mission.***

`tpub` is a mission-specific tool that enables NASA's TESS Guest Investigator 
Office to keep track of its mission's scientific publications in an easy way. 
It leverages SQLite and the [ADS API](https://github.com/adsabs/adsabs-dev-api)
(using Andy Casey's [awesome Python client](https://github.com/andycasey/ads)) 
to create and curate a database that contains the metadata 
of mission-related articles. This is a fork of kpub which is used to track Kepler/K2 publications. kpub was written by Geert Barentsen

## Example use

Print a nicely-formatted list of Kepler-related exoplanet publications in markdown format:
```
tpub --exoplanets
```

Add a new article to the database using its bibcode.
This command will display the article's metadata and ask the user to
classify the science:
```
tpub-add 2015arXiv150204715F
```

Remove an article using its bibcode:
```
tpub-delete 2015ApJ...800...46B
```

Search ADS interactively for new Kepler-related articles and try to add them:
```
tpub-update 2015-07
```

For example output, see the `data/output/` sub-directory in this repository.

## Installation

To install the latest version from source:
```
git clone https://github.com/tessgi/tpub.git
cd tpub
python setup.py install
```

Note that the `tpub` tools will use `~/.tpub.db` as the default database file.
This repository contains a recent version
of the database file (`data/tpub.db`),
which you may want to link to the default file as follows:
```
ln -s /path/to/git/repo/data/tpub.db ~/.tpub.db
```

The `tpub-add`and `tpub-update` tools that come with this package require
an api key from NASA ADS labs to retrieve publication meta-data.
You need to follow the installation instructions of the [ads client](https://github.com/andycasey/ads) by @andycasey to make this work.

## Usage

`tpub` adds a number of tools to the command line (described below).

There is a `Makefile` which makes your life easy if you work
for the GI office and are updating the database. 
Simply type:
* `make update` to search for new publications;
* `make push` to push the updated database to the git repo;
* `make refresh` to export and import all publications, this is slow and necessary only if you want to remove duplicates and fetch fresh citation statistics.

## Command-line tools

After installation, this package adds the following command-line tools to your path:
* `tpub` prints the list of publications in markdown format;
* `tpub-update` adds new publications by searching ADS (interactive);
* `tpub-add` adds a publication using its ADS bibcode;
* `tpub-delete` deletes a publication using its ADS bibcode;
* `tpub-import` imports bibcodes from a csv file;
* `tpub-export` exports bibcodes to a csv file;
* `tpub-plot` creates a visualization of the database;
* `tpub-spreadsheet` exports the publications to an Excel spreadsheet.

Listed below are the usage instructions for each command:

*tpub*
```
$ tpub --help
usage: kpub [-h] [-f dbfile] [-e] [-a] [-k] [-2] [-m]

View the TESS publication list in markdown format.

optional arguments:
  -h, --help          show this help message and exit
  -f dbfile           Location of the TESS publication list db. Defaults 
                      to ~/.tpub.db.
  -e, --exoplanets    Only show exoplanet publications.
  -a, --astrophysics  Only show astrophysics publications.
  -m, --month         Group the papers by month rather than year.
```

*kpub-update*
```
$ tpub-update --help
usage: tpub-update [-h] [-f dbfile] [month]

Interactively query ADS for new publications.

positional arguments:
  month       Month to query, e.g. 2015-06.

optional arguments:
  -h, --help  show this help message and exit
  -f dbfile   Location of the TESS publication list db. Defaults to
              ~/.tpub.db.
```

*tpub-add*
```
$ tpub-add --help
usage: tpub-add [-h] [-f dbfile] bibcode [bibcode ...]

Add a paper to the TESS publication list.

positional arguments:
  bibcode     ADS bibcode that identifies the publication.

optional arguments:
  -h, --help  show this help message and exit
  -f dbfile   Location of the TESS publication list db. Defaults to
              ~/.tpub.db.
```

*tpub-delete*
```
$ tpub-delete --help
usage: tpub-delete [-h] [-f dbfile] bibcode [bibcode ...]

Deletes a paper from the TESS publication list.

positional arguments:
  bibcode     ADS bibcode that identifies the publication.

optional arguments:
  -h, --help  show this help message and exit
  -f dbfile   Location of the TESS publication list db. Defaults to
              ~/.tpub.db.
```

*kpub-import*
```
$ tpub-import --help 
usage: tpub-import [-h] [-f dbfile] csvfile

Batch-import papers into the TESS publication list from a CSV file. The
CSV file must have three columns (bibcode,mission,science) separated by
commas. For example: '2004ApJ...610.1199G,tess,astrophysics'.

positional arguments:
  csvfile     Filename of the csv file to ingest.

optional arguments:
  -h, --help  show this help message and exit
  -f dbfile   Location of the TESS publication list db. Defaults to
              ~/.tpub.db.
```

*tpub-export*
```
$ tpub-export --help
usage: tpub-export [-h] [-f dbfile]

Export the TESS publication list in CSV format.

optional arguments:
  -h, --help  show this help message and exit
  -f dbfile   Location of the TESS publication list db. Defaults to
              ~/.tpub.db.
```

*tpub-spreadsheet*
```
$ tpub-spreadsheet --help
usage: tpub-spreadsheet [-h] [-f dbfile]

Export the TESS publication list in XLS format.

optional arguments:
  -h, --help  show this help message and exit
  -f dbfile   Location of the TESS publication list db. Defaults to
              ~/.tpub.db.
```

## Author
kpub was created by Geert Barentsen (geert.barentsen at nasa.gov)
on behalf of the Kepler/K2 Guest Observer Office.

tpub is a fork of kpub that creates a list of TESS publications, rather than Kepler/K2. 
The tpub fork was created by Tom Barclay (thomas.barclay at nasa.gov)
on behalf of the TESS Guest Investigator Office.

## Acknowledgements
This tool is made possible thanks to the efforts made by NASA ADS to
provide a web API, and thanks to the excellent Python client that Andy Casey
(@andycasey) wrote to use the API.

We also thank Geert cos he wrote nearly all the code here.
