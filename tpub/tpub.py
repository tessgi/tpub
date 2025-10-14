"""Build and maintain a database of TESS publications.
"""
from __future__ import print_function, division, unicode_literals

# Standard library
import os
import re
import sys
import json
import datetime
import argparse
import collections
import sqlite3 as sql
import numpy as np

try:
    import ads
except Exception:
    ads = None

# External dependencies
import jinja2
from six.moves import input  # needed to support Python 2
from astropy import log
from tqdm import tqdm

from . import plot, PACKAGEDIR

# Where is the default location of the SQLite database?
DEFAULT_DB = os.path.expanduser("~/.tpub.db")

# Which metadata fields do we want to retrieve from the ADS API?
# (basically everything apart from 'aff' and 'body' to reduce data volume)
FIELDS = ['date', 'pub', 'id', 'volume', 'links_data', 'citation', 'doi',
          'eid', 'keyword_schema', 'citation_count', 'year', 'identifier',
          'keyword_norm', 'reference', 'abstract', 'recid',
          'alternate_bibcode', 'arxiv_class', 'bibcode', 'first_author_norm',
          'pubdate', 'reader', 'doctype', 'title', 'pub_raw', 'property',
          'author', 'email', 'orcid', 'keyword', 'author_norm',
          'cite_read_boost', 'database', 'classic_factor', 'ack', 'page',
          'first_author', 'read_count', 'indexstamp', 'issue', 'keyword_facet',
          'aff']


class Highlight:
    """Defines colors for highlighting words in the terminal."""
    RED = "\033[4;31m"
    GREEN = "\033[4;32m"
    YELLOW = "\033[4;33m"
    BLUE = "\033[4;34m"
    PURPLE = "\033[4;35m"
    CYAN = "\033[4;36m"
    END = '\033[0m'


class PublicationDB(object):
    """Class wrapping the SQLite database containing the publications.

    Parameters
    ----------
    filename : str
        Path to the SQLite database file.
    """
    def __init__(self, filename=DEFAULT_DB):
        self.filename = filename
        self.con = sql.connect(filename)
        pubs_table_exists = self.con.execute(
                                """
                                   SELECT COUNT(*) FROM sqlite_master
                                   WHERE type='table' AND name='pubs';
                                """).fetchone()[0]
        if not pubs_table_exists:
            self.create_table()

    def create_table(self):
        self.con.execute("""CREATE TABLE pubs(
                                id UNIQUE,
                                bibcode UNIQUE,
                                year,
                                month,
                                date,
                                mission,
                                science,
                                metrics)""")

    def add(self, article, mission="tess", science="exoplanets"):
        """Adds a single article object to the database.

        Parameters
        ----------
        article : `ads.Article` object.
            An article object as returned by `ads.SearchQuery`.
        """
        log.debug('Ingesting {}'.format(article.bibcode))
        # Also store the extra metadata in the json string
        month = article.pubdate[0:7]
        article._raw['mission'] = mission
        article._raw['science'] = science
        try:
            cur = self.con.execute("INSERT INTO pubs "
                                   "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                   [article.id, article.bibcode,
                                    article.year, month, article.pubdate,
                                    mission, science,
                                    json.dumps(article._raw)])
            log.info('Inserted {} row(s).'.format(cur.rowcount))
            self.con.commit()
        except sql.IntegrityError:
            log.warning('{} was already ingested.'.format(article.bibcode))

    def add_interactively(self, article, statusmsg=""):
        """Adds an article by prompting the user for the classification.

        Parameters
        ----------
        article : `ads.Article` object
        """
        # Do not show an article that is already in the database
        if article in self:
            log.info("{} is already in the database "
                     "-- skipping.".format(article.bibcode))
            return

        # First, highlight keywords in the title and abstract
        colors = {'TESS': Highlight.BLUE,
                  'TIC': Highlight.BLUE,
                  'TOI': Highlight.BLUE,
                  'PLANET': Highlight.YELLOW,
                  'TRANSITING': Highlight.YELLOW,
                  'EXOPLANET': Highlight.YELLOW,
                  'SURVEY': Highlight.YELLOW,
                  'SATELLITE': Highlight.YELLOW,}
        title = article.title[0]
        try:
            abstract = article.abstract
        except AttributeError:
            abstract = ""

        for word in colors:
            pattern = re.compile(word, re.IGNORECASE)
            title = pattern.sub(colors[word] + word + Highlight.END, title)
            if abstract is not None:
                abstract = pattern.sub(colors[word]+word+Highlight.END, abstract)

        # Print paper information to stdout
        print(chr(27) + "[2J")  # Clear screen
        print(statusmsg)
        print(title)
        print('-'*len(title))
        print(abstract)
        print('')
        if article.author != None:
            print('Authors: ' + ', '.join(article.author))
        print('Date: ' + article.pubdate)
        print('Status: ' + str(article.property))
        print('URL: http://adsabs.harvard.edu/abs/' + article.bibcode)
        print('')

        # Prompt the user to classify the paper by mission and science
        print("=> TESS [1], unrelated [3], or skip [any key]? ",
              end="")
        prompt = input()
        if prompt == "1":
            mission = "tess"
        elif prompt == "3":
            mission = "unrelated"
        else:
            return
        print(mission)

        # Now classify by science
        science = ""
        if mission != "unrelated":
            print('=> Exoplanets [1] or Astrophysics [2]? ', end='')
            prompt = input()
            if prompt == "1":
                science = "exoplanets"
            elif prompt == "2":
                science = "astrophysics"
            print(science)

        self.add(article, mission=mission, science=science)

    def add_by_bibcode(self, bibcode, interactive=False, **kwargs):
        if ads is None:
            log.error("This action requires the ADS key to be setup.")
            return

        q = ads.SearchQuery(q="identifier:{}".format(bibcode), fl=FIELDS)
        for article in q:
            # Print useful warnings
            if bibcode != article.bibcode:
                log.warning("Requested {} but ADS API returned {}".format(bibcode, article.bibcode))
            if article.property is None:
                log.warning("{} returned None for article.property.".format(article.bibcode))
            elif 'NONARTICLE' in article.property:
                # Note: data products are sometimes tagged as NONARTICLE
                log.warning("{} is not an article.".format(article.bibcode))

            if article in self:
                log.warning("{} is already in the db.".format(article.bibcode))
            else:
                if interactive:
                    self.add_interactively(article)
                else:
                    self.add(article, **kwargs)

    def delete_by_bibcode(self, bibcode):
        cur = self.con.execute("DELETE FROM pubs WHERE bibcode = ?;", [bibcode])
        log.info('Deleted {} row(s).'.format(cur.rowcount))
        self.con.commit()

    def __contains__(self, article):
        count = self.con.execute("SELECT COUNT(*) FROM pubs WHERE id = ?;",
                                 [article.id]).fetchone()[0]
        return bool(count)

    def query(self, mission='tess', science=None):
        """Query the database by mission and/or science.

        Returns
        -------
        rows : list
            List of SQLite result rows.
        """
        # Build the query
        if mission is None:
            where = "(mission = 'tess') "
        else:
            where = "(mission = '{}') ".format(mission)

        if science is not None:
            where += " AND science = '{}' ".format(science)

        cur = self.con.execute("SELECT year, month, metrics, bibcode "
                               "FROM pubs "
                               "WHERE {} "
                               "ORDER BY date DESC; ".format(where))
        return cur.fetchall()

    def to_markdown(self, title="Publications",
                    group_by_month=False, save_as=None, **kwargs):
        """Returns the publication list in markdown format.
        """
        if group_by_month:
            group_idx = 1
        else:
            group_idx = 0  # by year

        articles = collections.OrderedDict({})
        for row in self.query(**kwargs):
            group = row[group_idx]
            if group.endswith("-00"):
                group = group[:-3] + "-01"
            if group not in articles:
                articles[group] = []
            art = json.loads(row[2])
            # The markdown template depends on "property" being iterable
            if art["property"] is None:
                art["property"] = []
            articles[group].append(art)

        templatedir = os.path.join(PACKAGEDIR, 'templates')
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(templatedir))
        template = env.get_template('template.md')
        markdown = template.render(title=title, save_as=save_as,
                                   articles=articles)
        if sys.version_info >= (3, 0):
            return markdown  # Python 3
        else:
            return markdown.encode("utf-8")  # Python 2

    def save_markdown(self, output_fn, **kwargs):
        """Saves the database to a text file in markdown format.

        Parameters
        ----------
        output_fn : str
            Path of the file to write.
        """
        markdown = self.to_markdown(save_as=output_fn.replace("md", "html"),
                                    **kwargs)
        log.info('Writing {}'.format(output_fn))
        f = open(output_fn, 'w')
        f.write(markdown)
        f.close()

    def plot(self):
        """Saves beautiful plot of the database."""
        for extension in ['pdf', 'png']:
            plot.plot_by_year(self,
                              "tpub-publication-rate.{}".format(extension))
            plot.plot_by_year(self,
                              "tpub-publication-rate-without-extrapolation.{}".format(extension),
                              extrapolate=False)
            plot.plot_science_piechart(self,
                                       "tpub-piechart.{}".format(extension))

    def get_metrics(self):
        """Returns a dictionary of overall publication statistics.

        The metrics include:
        * # of publications since XX.
        * # of unique author surnames.
        * # of citations.
        * # of peer-reviewed pubs.
        * # of exoplanet/astrophysics.
        """
        metrics = {
                   "publication_count": 0,
                   "tess_count": 0,
                   "exoplanets_count": 0,
                   "astrophysics_count": 0,
                   "refereed_count": 0,
                   "tess_refereed_count": 0,
                   "citation_count": 0
                   }
        first_authors, authors = [], []
        tess_authors = list()
        for article in self.query():
            api_response = article[2]
            js = json.loads(api_response)
            metrics["publication_count"] += 1
            metrics["{}_count".format(js["mission"])] += 1
            try:
                metrics["{}_count".format(js["science"])] += 1
            except KeyError:
                log.warning("{}: no science category".format(js["bibcode"]))
            first_authors.append(js["first_author_norm"])
            authors.extend(js["author_norm"])
            if js["mission"] == 'tess':
                tess_authors.extend(js["author_norm"])
            else:
                tess_authors.extend(js["author_norm"])
            try:
                if "REFEREED" in js["property"]:
                    metrics["refereed_count"] += 1
                    metrics["{}_refereed_count".format(js["mission"])] += 1
            except TypeError:  # proprety is None
                pass
            try:
                metrics["citation_count"] += js["citation_count"]
            except (KeyError, TypeError):
                log.warning("{}: no citation_count".format(js["bibcode"]))
        metrics["first_author_count"] = np.unique(first_authors).size
        metrics["author_count"] = np.unique(authors).size
        metrics["tess_author_count"] = np.unique(tess_authors).size
        # Also compute fractions
        for frac in ["tess", "exoplanets", "astrophysics"]:
            metrics[frac+"_fraction"] = metrics[frac+"_count"] / metrics["publication_count"]
        return metrics

    def get_most_cited(self, mission=None, science=None, top=10):
        """Returns the most-cited publications."""
        bibcodes, citations = [], []
        articles = self.query(mission=mission, science=science)
        for article in articles:
            api_response = article[2]
            js = json.loads(api_response)
            bibcodes.append(article[3])
            citations.append(js["citation_count"])
        idx_top = np.argsort(citations)[::-1][0:top]
        return [json.loads(articles[idx][2]) for idx in idx_top]

    def get_most_read(self, mission=None, science=None, top=10):
        """Returns the most-cited publications."""
        bibcodes, citations = [], []
        articles = self.query(mission=mission, science=science)
        for article in articles:
            api_response = article[2]
            js = json.loads(api_response)
            bibcodes.append(article[3])
            citations.append(js["read_count"])
        idx_top = np.argsort(citations)[::-1][0:top]
        return [json.loads(articles[idx][2]) for idx in idx_top]

    def get_most_active_first_authors(self, min_papers=6):
        """Returns names and paper counts of the most active first authors."""
        articles = self.query()
        authors = {}
        for article in articles:
            api_response = article[2]
            js = json.loads(api_response)
            first_author = js["first_author_norm"]
            try:
                authors[first_author] += 1
            except KeyError:
                authors[first_author] = 1
        names = np.array(list(authors.keys()))
        paper_count = np.array(list(authors.values()))
        idx_top = np.argsort(paper_count)[::-1]
        mask = paper_count[idx_top] >= min_papers
        return zip(names[idx_top], paper_count[idx_top[mask]])

    def get_all_authors(self, top=20):
        articles = self.query()
        authors = {}
        for article in articles:
            api_response = article[2]
            js = json.loads(api_response)
            for auth in js["author_norm"]:
                try:
                    authors[auth] += 1
                except KeyError:
                    authors[auth] = 1
        names = np.array(list(authors.keys()))
        paper_count = np.array(list(authors.values()))
        idx_top = np.argsort(paper_count)[::-1][:top]
        return names[idx_top], paper_count[idx_top]

    def update(self, month=None,
                exclude=['johannes']
               # exclude=['keplerian', 'johannes', 'k<sub>2</sub>',
               #          "kepler equation", "kepler's equation", "xmm-newton",
               #          "kepler's law", "kepler's third law", "kepler problem",
               #          "kepler crater", "kepler's supernova", "kepler's snr"]
               ):
        """Query ADS for new publications.

        Parameters
        ----------
        month : str
            Of the form "YYYY-MM".

        exclude : list of str
            Ignore articles if they contain any of the strings given
            in this list. (Case-insensitive.)
        """
        if ads is None:
            log.error("This action requires the ADS key to be setup.")
            return

        print(Highlight.YELLOW +
              "Reminder: did you `git pull` tpub before running "
              "this command? [y/n] " +
              Highlight.END,
              end='')
        if input() == 'n':
            return

        if month is None:
            month = datetime.datetime.now().strftime("%Y-%m")

        # First show all the papers with the TESS funding message in the ack
        log.info("Querying ADS for acknowledgements (month={}).".format(month))
        database = "astronomy"
        qry = ads.SearchQuery(q="""(ack:"TESS mission"
                                    OR ack:"Transiting Exoplanet Survey Satellite"
                                    OR ack:"TESS team"
                                    OR ack:"TESS")
                                   -ack:"partial support from"
                                   pubdate:"{}"
                                   database:"{}"
                                """.format(month, database),
                              fl=FIELDS,
                              rows=9999999999)
        articles = list(qry)
        for idx, article in enumerate(articles):
            statusmsg = ("Showing article {} out of {} that mentions TESS "
                         "in the acknowledgements.\n\n".format(
                            idx+1, len(articles)))
            self.add_interactively(article, statusmsg=statusmsg)

        # Then search for keywords in the title and abstracts
        log.info("Querying ADS for titles and abstracts "
                 "(month={}).".format(month))
        qry = ads.SearchQuery(q="""(
                                    abs:"TESS"
                                    OR abs:"Transiting Exoplanet Survey Satellite"
                                    OR title:"TESS"
                                    OR title:"Transiting Exoplanet Survey Satellite"
                                    OR full:"TESS photometry"
                                    OR full:"TESS lightcurve"
                                    )
                                   pubdate:"{}"
                                   database:"{}"
                                """.format(month, database),
                              fl=FIELDS,
                              rows=9999999999)
        articles = list(qry)

        for idx, article in enumerate(articles):
            # Ignore articles without abstract
            if not hasattr(article, 'abstract') or article.abstract is None:
                continue
            abstract_lower = article.abstract.lower()

            ignore = False

            # Ignore articles containing any of the excluded terms
            for term in exclude:
                if term.lower() in abstract_lower:
                    ignore = True

            # Ignore articles already in the database
            if article in self:
                ignore = True

            # Ignore all the unrefereed non-arxiv stuff
            try:
                if "NOT REFEREED" in article.property and article.pub.lower() != "arxiv e-prints":
                    ignore = True
            except (AttributeError, TypeError, ads.exceptions.APIResponseError):
                pass  # no .pub attribute

            # Ignore proposals and cospar abstracts
            if ".prop." in article.bibcode or "cosp.." in article.bibcode:
                ignore = True

            if not ignore:  # Propose to the user
                statusmsg = '(Reviewing article {} out of {}.)\n\n'.format(
                                idx+1, len(articles))
                self.add_interactively(article, statusmsg=statusmsg)
        log.info('Finished reviewing all articles for {}.'.format(month))


def tpub(args=None):
    """Lists the publications in the database in Markdown format."""
    parser = argparse.ArgumentParser(
        description="View the TESS publication list in markdown format.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the TESS publication list db. "
                             "Defaults to ~/.tpub.db.")
    parser.add_argument('-e', '--exoplanets', action='store_true',
                        help='Only show exoplanet publications.')
    parser.add_argument('-a', '--astrophysics', action='store_true',
                        help='Only show astrophysics publications.')
    parser.add_argument('-m', '--month', action='store_true',
                        help='Group the papers by month rather than year.')
    parser.add_argument('-s', '--save', action='store_true',
                        help='Save the output and plots in the current directory.')
    args = parser.parse_args(args)

    db = PublicationDB(args.f)

    if args.save:
        for bymonth in [True, False]:
            if bymonth:
                suffix = "-by-month"
                title_suffix = " by month"
            else:
                suffix = ""
                title_suffix = ""
            output_fn = 'tpub{}.md'.format(suffix)
            db.save_markdown(output_fn,
                             group_by_month=bymonth,
                             title="TESS publications{}".format(title_suffix))
            for science in ['exoplanets', 'astrophysics']:
                output_fn = 'tpub-{}{}.md'.format(science, suffix)
                db.save_markdown(output_fn,
                                 group_by_month=bymonth,
                                 science=science,
                                 title="TESS {} publications{}".format(science, title_suffix))

        # Finally, produce an overview page
        templatedir = os.path.join(PACKAGEDIR, 'templates')
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(templatedir))
        template = env.get_template('template-overview.md')
        markdown = template.render(metrics=db.get_metrics(),
                                   most_cited=db.get_most_cited(top=10),
                                   most_active_first_authors=db.get_most_active_first_authors(),
                                   now=datetime.datetime.now())
        # most_read=db.get_most_read(20),
        filename = 'publications.md'
        log.info('Writing {}'.format(filename))
        f = open(filename, 'w')
        if sys.version_info >= (3, 0):
            f.write(markdown)  # Python 3
        else:
            f.write(markdown.encode("utf-8"))  # Legacy Python
        f.close()

    else:
        if args.exoplanets and not args.astrophysics:
            science = "exoplanets"
        elif args.astrophysics and not args.exoplanets:
            science = "astrophysics"
        else:
            science = None


        mission = None

        output = db.to_markdown(group_by_month=args.month,
                                mission=mission,
                                science=science)
        from signal import signal, SIGPIPE, SIG_DFL
        signal(SIGPIPE, SIG_DFL)
        print(output)


def tpub_plot(args=None):
    """Creates beautiful plots of the database."""
    parser = argparse.ArgumentParser(
        description="Creates beautiful plots of the database.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the TESS publication list db. "
                             "Defaults to ~/.tpub.db.")
    args = parser.parse_args(args)

    PublicationDB(args.f).plot()


def tpub_update(args=None):
    """Interactively query ADS for new publications."""
    parser = argparse.ArgumentParser(
        description="Interactively query ADS for new publications.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the TESS publication list db. "
                             "Defaults to ~/.tpub.db.")
    parser.add_argument('month', nargs='?', default=None,
                        help='Month to query, e.g. 2015-06.')
    args = parser.parse_args(args)

    PublicationDB(args.f).update(month=args.month)


def tpub_add(args=None):
    """Add a publication with a known ADS bibcode."""
    parser = argparse.ArgumentParser(
        description="Add a paper to the TESS publication list.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the TESS publication list db. "
                             "Defaults to ~/.tpub.db.")
    parser.add_argument('bibcode', nargs='+',
                        help='ADS bibcode that identifies the publication.')
    args = parser.parse_args(args)

    db = PublicationDB(args.f)
    for bibcode in args.bibcode:
        db.add_by_bibcode(bibcode, interactive=True)


def tpub_delete(args=None):
    """Deletes a publication using its ADS bibcode."""
    parser = argparse.ArgumentParser(
        description="Deletes a paper from the TESS publication list.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the TESS publication list db. "
                             "Defaults to ~/.tpub.db.")
    parser.add_argument('bibcode', nargs='+',
                        help='ADS bibcode that identifies the publication.')
    args = parser.parse_args(args)

    db = PublicationDB(args.f)
    for bibcode in args.bibcode:
        db.delete_by_bibcode(bibcode)


def tpub_import(args=None):
    """Import publications from a csv file.

    The csv file must contain entries of the form "bibcode,mission,science".
    The actual metadata of each publication will be grabbed using the ADS API,
    hence this routine may take 10-20 minutes to complete.
    """
    parser = argparse.ArgumentParser(
        description="Batch-import papers into the TESS publication list "
                    "from a CSV file. The CSV file must have three columns "
                    "(bibcode,mission,science) separated by commas. "
                    "For example: '2004ApJ...610.1199G,tess,astrophysics'.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the TESS publication list db. "
                             "Defaults to ~/.tpub.db.")
    parser.add_argument('csvfile',
                        help="Filename of the csv file to ingest.")
    args = parser.parse_args(args)

    db = PublicationDB(args.f)
    for line in tqdm(open(args.csvfile, 'r').readlines()):
        col = line.split(',')  # Naive csv parsing
        db.add_by_bibcode(col[0], mission=col[1], science=col[2].strip())


def tpub_export(args=None):
    """Export the bibcodes and classifications in CSV format."""
    parser = argparse.ArgumentParser(
        description="Export the TESS publication list in CSV format.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the TESS publication list db. "
                             "Defaults to ~/.tpub.db.")
    args = parser.parse_args(args)

    db = PublicationDB(args.f)
    cur = db.con.execute("SELECT bibcode, mission, science "
                         "FROM pubs ORDER BY bibcode;")
    for row in cur.fetchall():
        print('{0},{1},{2}'.format(row[0], row[1], row[2]))


def tpub_spreadsheet(args=None):
    """Export the publication database to an Excel spreadsheet."""
    try:
        import pandas as pd
    except ImportError:
        print('ERROR: pandas needs to be installed for this feature.')

    parser = argparse.ArgumentParser(
        description="Export the TESS publication list in XLS format.")
    parser.add_argument('-f', metavar='dbfile',
                        type=str, default=DEFAULT_DB,
                        help="Location of the TESS publication list db. "
                             "Defaults to ~/.tpub.db.")
    args = parser.parse_args(args)

    db = PublicationDB(args.f)
    spreadsheet = []
    cur = db.con.execute("SELECT bibcode, year, month, date, mission, science, metrics "
                         "FROM pubs WHERE mission != 'unrelated' ORDER BY bibcode;")
    for row in cur.fetchall():
        metrics = json.loads(row[6])
        if 'REFEREED' in metrics['property']:
            refereed = 'REFEREED'
        elif 'NOT REFEREED' in metrics['property']:
            refereed = 'NOT REFEREED'
        else:
            refereed = ''
        myrow = collections.OrderedDict([
                    ('bibcode', row[0]),
                    ('year', row[1]),
                    ('date', row[3]),
                    ('mission', row[4]),
                    ('science', row[5]),
                    ('refereed', refereed),
                    ('citation_count', metrics['citation_count']),
                    ('first_author_norm', metrics['first_author_norm']),
                    ('title', metrics['title'][0])])
        spreadsheet.append(myrow)

    output_fn = 'tess-publications.xls'
    print('Writing {}'.format(output_fn))
    pd.DataFrame(spreadsheet).to_excel(output_fn, index=False)


if __name__ == '__main__':
    pass
