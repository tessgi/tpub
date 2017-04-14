import datetime
import tpub

def print_articles(articles):
    for idx, art in enumerate(articles):
        print("{}. {}\n{} ({})\n{} citations\n".format(idx+1,
                                                       art["title"][0].upper(),
                                                       art['first_author_norm'],
                                                       art['bibcode'],
                                                       art['citation_count']))


if __name__ == "__main__":
    db = tpub.PublicationDB()
    articles = db.get_most_cited(mission="tess", top=10)
    print("THE 10 MOST CITED TESS PAPERS\n"
          "===========================\n"
          "Last update: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d")))
    print_articles(articles)

